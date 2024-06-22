import flet as ft
from flet_core.icons import DARK_MODE
import requests
from bs4 import BeautifulSoup
import os
import re
import threading
import json
import platform
import time

# Constants
NOTHING_COLOR = "#D71921"
DECOR = ' ::'
HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
STATE_FILE = "app_state.json"
CATEGORIES = {
        'Sha3\'af': 'https://msc-mu.com/level/18',
        'Athar': 'https://msc-mu.com/level/17',
        'Rou7': 'https://msc-mu.com/level/16',
        'Wateen': 'https://msc-mu.com/level/15',
        'Nabed': 'https://msc-mu.com/level/14',
        'Wareed': 'https://msc-mu.com/level/13',
        'Minors': 'https://msc-mu.com/level/10',
        'Majors': 'https://msc-mu.com/level/9'
        }

class Scraper:
    def __init__(self):
        pass

    def find_courses(self, url):
        page = requests.get(url, headers=HEADERS)
        doc = BeautifulSoup(page.text, 'html.parser')
        subject = doc.find_all('h6')
        courses = []
        for x, i in enumerate(subject):
            parent = i.parent.parent.parent
            course_number = re.findall('href="https://msc-mu.com/courses/(.*)">', parent.decode())[0]
            course_name = i.string.strip()
            courses.append([x + 1, course_name, course_number])
        return courses

    def create_nav_links_dictionary(self, soup):
        navigate_dict = {}
        nav_links = soup.find_all('li', attrs={"class": "nav-item"})
        for navigate_link in nav_links:
            if navigate_link.h5:
                nav_name = navigate_link.h5.text.strip()
                nav_number = navigate_link.a.get('aria-controls')
                navigate_dict[nav_number] = nav_name
        return navigate_dict

    def make_course_folder(self, folder, course_name):
        new_folder = os.path.join(folder, course_name)
        if not os.path.isdir(new_folder):
            os.mkdir(new_folder)
        return new_folder

    def find_files_paths_and_links(self, navigation_dict, soup, file_types):
        file_tags = []
        for file_type in file_types:
            file_tags.extend(soup.find_all('a', string=lambda text: text and file_type in text))

        files_list = []
        path = []
        associated_nav_link_id = ''
        for file_tag in file_tags:
            current_tag = file_tag
            if not current_tag:
                print('No files found for the selected extensions!')
                quit()
            while True:
                current_tag = current_tag.parent
                if current_tag.name == 'div' and 'mb-3' in current_tag.get('class', []):
                    path.append(current_tag.h6.text.strip())
                if current_tag.name == 'div' and 'tab-pane' in current_tag.get('class', []):
                    associated_nav_link_id = current_tag.get('id')
                if not current_tag.parent:
                    break
            path.append(navigation_dict[associated_nav_link_id])
            path.reverse()
            basename = file_tag.text
            file_path = "/".join(path) + os.path.sep
            path.clear()

            file_link = file_tag.get('href')
            files_list.append([file_path, file_link, basename])
        return files_list


    def download_from_dict(self, path_link_dict, folder, progress_container, downloading_listview, already_downloaded_listview):
        counter = 0
        total_files = len(path_link_dict)

        for path, link, name in path_link_dict:
            counter += 1
            count = f' ({counter}/{total_files})'
            full_path = os.path.join(folder, path)

            if os.path.isfile(os.path.join(full_path, name)):
                print('[ Already there! ] ' + name + count)
                already_downloaded_listview.controls.append(ft.Text(name, color="white"))
                already_downloaded_listview.update()
                continue

            if not os.path.isdir(full_path):
                os.makedirs(full_path)

            response = requests.get(link, headers=HEADERS)
            with open(os.path.join(full_path, name), 'wb') as file:
                file.write(response.content)
            print(DECOR + ' Downloaded ' + name + count)
            downloading_listview.controls.append(ft.Text(name, color="white"))
            downloading_listview.update()

            # Update the progress bar
            progress = counter / total_files
            progress_container.content.value = progress
            progress_container.update()

def get_default_download_directory():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.environ["USERPROFILE"], "Downloads")
    elif system == "Darwin":  # macOS
        return os.path.join(os.environ["HOME"], "Downloads")
    elif system == "Linux" and "ANDROID_STORAGE" not in os.environ:
        return os.path.join(os.environ["HOME"], "Downloads")
    elif system == "Linux" and "ANDROID_STORAGE" in os.environ:
        return "/storage/emulated/0/Download"
    elif system == "iOS":
        # iOS file system is sandboxed and more complex to access, placeholder path
        return "/var/mobile/Containers/Data/Application/Downloads"
    else:
        raise Exception("Unsupported OS")

def show_dialog(page, title, message):
    dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            )
    page.dialog = dlg
    page.dialog.open = True
    page.update()

def main(page: ft.Page):
    dark_mode = True
    page.fonts = {
            "Nothing": "assets/Nothing.ttf",
            }
    page.icon = "assets/icon.png"
    page.title = "STUKA"
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    # Defining event handlers

    def category_selected(e):
        course_dropdown.visible = False
        course_dropdown.value = ""
        course_dropdown.update()
        url = CATEGORIES[e.data]
        courses = scraper.find_courses(url)
        course_dropdown.options = [ft.dropdown.Option(course[1]) for course in courses]
        course_dropdown.visible = True
        course_dropdown.update()

    def start_download(e):
        category_name = category_dropdown.value
        course_name = course_dropdown.value
        folder = folder_field.value


        selected_file_types = []
        if pdf_checkbox.value:
            selected_file_types.append('.pdf')

        if ppt_checkbox.value:
            selected_file_types.append('.ppt')

        if category_name == "Select a category":
            show_dialog(page, "Error", "Please select a category.")
            return

        if not course_name:
            show_dialog(page, "Error", "Please select a course.")
            return

        if not folder:
            folder = get_default_download_directory()
            folder_field.value = folder
            folder_field.update()

        if not selected_file_types:
            show_dialog(page, "Error", "Please select at least one file type to download.")
            return

        download_btn.disabled = True
        download_btn.update()
        downloading_card.visible = True
        already_card.visible = True
        page.update()

        category_url = CATEGORIES[category_name]
        try:
            courses = scraper.find_courses(category_url)
        except Exception as e:
            show_dialog(page, "Error", f"Failed to fetch courses: {e}")
            return

        course_number = next(course[2] for course in courses if course[1] == course_name)
        download_folder = scraper.make_course_folder(folder, course_name)
        download_url = 'https://msc-mu.com/courses/' + course_number

        def download_thread():
            try:
                print(DECOR + ' Requesting page...')
                geeky_listview.controls.append(ft.Text(DECOR + ' Requesting page...', color="white"))
                geeky_listview.update()
                course_page = requests.get(download_url, headers=HEADERS)
                print(DECOR + ' Parsing page into a soup...')
                geeky_listview.controls.append(ft.Text(DECOR + ' Parsing page into a soup...', color="white"))
                geeky_listview.update()
                soup = BeautifulSoup(course_page.text, 'html.parser')
                nav_dict = scraper.create_nav_links_dictionary(soup)
                file_dict = scraper.find_files_paths_and_links(nav_dict, soup, selected_file_types)

                progress_container.visible = True
                scraper.download_from_dict(file_dict, download_folder, progress_container, downloading_listview, already_downloaded_listview)
                progress_container.visible = False  # Hide progress bar after download completes
                show_dialog(page, "Success", "Download complete!")
                download_btn.disabled = False
                download_btn.update()
                downloading_card.visible = False
                already_card.visible = False
                page.update()

            except Exception as e:
                progress_container.visible = False  # Ensure progress bar is hidden on error
                download_btn.disabled = True
                show_dialog(page, "Error", f"An error occurred: {e}")

        # Start download thread
        threading.Thread(target=download_thread).start()



    def toggle_geek(e):
        if geeky_card.visible == False:
            geeky_card.visible = True
        else:
            geeky_card.visible = False
        geeky_card.update()

    def toggle_dark_mode(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            dark_mode = False
        else:
            dark_mode = True
        set_custom_theme(page, dark_mode)

    def set_custom_theme(page, dark_mode):
        if dark_mode:
            page.theme_mode = ft.ThemeMode.DARK
            page.dark_theme = ft.Theme(
                    use_material3=True,
                    font_family="Nothing",
                    visual_density="comfortable",
                    )
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.theme = ft.Theme(
                    use_material3=True,
                    font_family="Nothing",
                    visual_density="comfortable",
                    )
        page.update()

    # Defining UI elements:

    set_custom_theme(page, dark_mode=True)

    category_dropdown = ft.dropdown.Dropdown(
            label="Category",
            label_style=ft.TextStyle(color="white"),
            options=[ft.dropdown.Option(key=key, text=key) for key in CATEGORIES.keys()],
            value="Select a category",
            on_change=category_selected,
            focused_border_color="#5C0000",

            )

    course_dropdown = ft.dropdown.Dropdown(
            label="Course",
            label_style=ft.TextStyle(color="white"),
            options=[],
            visible=False,
            focused_border_color="#5C0000",
            )

    # TODO make a killswitch so that stupid niggas can fuck the app.
    folder_field = ft.TextField(
            label="Destination Folder",
            visible=False
            )

    pdf_checkbox = ft.Checkbox(label="PDF",
                               value=True,
                               active_color="#5C0000",
                               check_color="white"
                               )

    ppt_checkbox = ft.Checkbox(label="PPT",
                               value=True,
                               active_color="#5C0000",
                               check_color="white"
                               )

    downloading_listview = ft.ListView(height=100, width=400, auto_scroll=True)

    already_downloaded_listview = ft.ListView(height=100, width=400, auto_scroll=True)

    geeky_listview = ft.ListView(height=75, width=400, auto_scroll=True)

    downloading_card = ft.Card(
            visible=False,
            color=NOTHING_COLOR,
            elevation=4,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.icons.DOWNLOAD, color="white"),
                            ft.Text("Downloading...", size=20 , color="white"),
                            ]),
                        downloading_listview,
                        ]
                    ),
                border_radius = 10,
                padding= 10,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[
                        "#8B0000",
                        "#1C000E"
                        ]
                    ),
                ),
            )

    already_card = ft.Card(
            visible=False,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.icons.ALBUM, color="white"),
                            ft.Text("Already downloaded:", size=20, color="white"),
                            ]),
                        already_downloaded_listview,
                        ]
                    ),
                border_radius = 10,
                padding= 10,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[
                        "#8B0000",
                        "#1C000E"
                        ]
                    ),
                ),
            color=NOTHING_COLOR,
            )

    geeky_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.icons.TERMINAL, color="white"),
                            ft.Text("What's going on >>", size=20, color="white"),
                            ]),
                        geeky_listview,
                        ]
                    ),
                padding= 10,
                border_radius= 10,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[
                        "#000000",
                        "#222222"
                        ]
                    ),
                ),
            color="black",
            visible=True,
            )

    download_btn = ft.ElevatedButton(
            text="Download",
            bgcolor="#5C0000",
            color=ft.colors.WHITE,
            on_click=start_download,

            )

    geeky_btn = ft.ElevatedButton(
            text="Hide details",
            bgcolor="#000000",
            color=ft.colors.WHITE,
            on_click=toggle_geek
            )

    progress_container = ft.Container(
            visible=False,
            padding=ft.padding.symmetric(0,10),
            content=ft.ProgressBar(
                value=0,
                width=600,
                bar_height=10,
                border_radius=ft.border_radius.all(10),
                color="#5C0000",
                bgcolor="#000000",
                ),
            )

    app_bar = ft.AppBar(
            title=ft.Text("COURSE DOWNLOADER", color="white"),
            center_title=True,
            bgcolor="#1B1B1D",
            actions=[
                ft.IconButton(
                    icon=ft.icons.BRIGHTNESS_4,
                    tooltip="Toggle Dark Mode",
                    on_click=toggle_dark_mode,
                    )
                ])

    # Adding elements to the page:

    page.add(
            app_bar,
            ft.Container(
                ft.Column(
                    controls=[
                        category_dropdown,
                        course_dropdown,
                        folder_field,
                        ft.Row(controls=[pdf_checkbox,ppt_checkbox]),
                        ft.Row(controls=[download_btn,geeky_btn]),
                        geeky_card,
                        progress_container,
                        downloading_card,
                        already_card,
                        ]
                    ),
                padding=10
                )
            )

scraper = Scraper()

ft.app(target=main, assets_dir="assets")
