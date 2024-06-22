import flet as ft
import requests
from bs4 import BeautifulSoup
import os
import re
import threading
import json
import time
import platform

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

test_list = [1,2,3,4,5,6,7,8,9,]

class Scraper:
    def __init__(self):
        pass

    def load_state(self):
        pass

    def save_state(self):
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


    def download_from_dict(self, path_link_dict, folder, progress_bar, downloading_listview, already_downloaded_listview):
        counter = 0
        total_files = len(path_link_dict)

        for path, link, name in path_link_dict:
            counter += 1
            count = f' ({counter}/{total_files})'
            full_path = os.path.join(folder, path)

            if os.path.isfile(os.path.join(full_path, name)):
                print('[ Already there! ] ' + name + count)
                already_downloaded_listview.controls.append(ft.Text(name))
                already_downloaded_listview.update()
                continue

            if not os.path.isdir(full_path):
                os.makedirs(full_path)

            response = requests.get(link, headers=HEADERS)
            with open(os.path.join(full_path, name), 'wb') as file:
                file.write(response.content)
            print(DECOR + ' Downloaded ' + name + count)
            downloading_listview.controls.append(ft.Text(name))
            downloading_listview.update()

            # Update the progress bar
            progress = counter / total_files
            progress_bar.value = progress
            progress_bar.update()


def main(page: ft.Page):
    page.fonts = {
            "Nothing": "assets/Nothing.ttf",
            }
    page.icon = "assets/icon.png"
    page.title = "STUKA"
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    # Defining event handlers

    def category_selected(e):
        url = CATEGORIES[e.data]
        courses = scraper.find_courses(url)
        print(courses)
        course_dropdown.options = [ft.dropdown.Option(course[1]) for course in courses]
        course_dropdown.visible = True
        course_dropdown.update()
        print("the shit should be shown by now")

    def start_download(e):
        pass

    def toggle_geek(e):
        if e.control.visible = False:
            geeky_card.visible = False


    def toggle_dark_mode(e):
        pass

    # Defining UI elements:

    category_dropdown = ft.dropdown.Dropdown(
            label="Category",
            options=[ft.dropdown.Option(key=key, text=key) for key in CATEGORIES.keys()],
            value="Select a category",
            on_change=category_selected,
            )

    course_dropdown = ft.dropdown.Dropdown(
            label="Course",
            options=[],
            visible=False
            )

    folder_field = ft.TextField(
            label="Destination Folder",
            visible=False
            )

    pdf_checkbox = ft.Checkbox(label="PDF", tristate=True)
    ppt_checkbox = ft.Checkbox(label="PPT", tristate=True)

    downloading_listview = ft.ListView(height=125, width=400)
    already_downloaded_listview = ft.ListView(height=125, width=400)
    geeky_listview = ft.ListView(height=75, width=400)

    downloading_card = ft.Card(content=ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.icons.DOWNLOAD),
                    ft.Text("Downloading...", size=20 ),
                    ]),
                downloading_listview,
                ]
            ),
        padding= 10,
        ),
                               color=NOTHING_COLOR,
                               )

    already_card = ft.Card(content=ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.icons.ALBUM),
                    ft.Text("Already downloaded:", size=20),
                    ]),
                already_downloaded_listview,
                ]
            ),
        padding= 10,
        ),
                           color=NOTHING_COLOR,
                           )

    geeky_card = ft.Card(content=ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.icons.TERMINAL),
                    ft.Text("What's going on >", size=20 ),
                    ]),
                geeky_listview,
                ]
            ),
        padding= 10,
        ),
                         color="black",
                         visible=True,

                         )

    download_btn = ft.ElevatedButton(
            text="Download",
            bgcolor=NOTHING_COLOR,
            color=ft.colors.WHITE,
            on_click=start_download
            )

    geeky_btn = ft.ElevatedButton(
            text="Hide details",
            bgcolor=NOTHING_COLOR,
            color=ft.colors.WHITE,
            on_click=toggle_geek
            )

    progress_bar = ft.ProgressBar(
            value=0,
            width=600,
            bar_height=10,
            border_radius=ft.border_radius.all(10),
            visible=False
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
            ft.Column(
                controls=[
                    category_dropdown,
                    course_dropdown,
                    folder_field,
                    ft.Row(controls=[pdf_checkbox,ppt_checkbox]),
                    ft.Row(controls=[download_btn,geeky_btn]),
                    geeky_card,
                    downloading_card,
                    already_card,
                    progress_bar,
                    ]
                )
            )



scraper = Scraper()

ft.app(target=main, assets_dir="assets")
