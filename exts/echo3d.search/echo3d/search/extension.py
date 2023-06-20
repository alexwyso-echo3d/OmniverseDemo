import os
import omni.ext
import omni.ui as ui
import omni.kit.commands
from pip_prebundle import requests
from omni.ui import color as cl

# GLOBAL VARIABLES
IMAGES_PER_PAGE = 3
current_search_page = 0
current_project_page = 0
search_image_widgets = [ui.Image() for _ in range(IMAGES_PER_PAGE)]
project_image_widgets = [ui.Image() for _ in range(IMAGES_PER_PAGE)]
searchJsonData = []
projectJsonData = []


###########################################################################################################
#                                                                                                         #
#   An extension for Nvidia Omniverse that allows users to connect to their echo3D projects in order to   #
#   stream their existing assets into the Omniverse Viewport, as well as search for new assets in the     #
#   echo3D public asset library to add to their projects.                                                 #
#                                                                                                         #
###########################################################################################################
class Echo3dSearchExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[echo3D] echo3D startup")

        ###############################################
        #     Define Functions for Search Feature     #
        ###############################################

        # Load in new image thumbnails when clicks the previous/next buttons
        def update_search_images(searchJsonData):
            start_index = current_search_page * IMAGES_PER_PAGE
            end_index = start_index + IMAGES_PER_PAGE
            for i in range(start_index, end_index):
                if i < len(searchJsonData):
                    search_image_widgets[i % IMAGES_PER_PAGE].source_url = searchJsonData[i]["thumbnail"]
                else:
                    search_image_widgets[i % IMAGES_PER_PAGE].source_url = ""

        def on_click_left_arrow_search():
            global current_search_page
            current_search_page -= 1
            global searchJsonData
            update_search_images(searchJsonData)

        def on_click_right_arrow_search():
            global current_search_page
            current_search_page += 1
            global searchJsonData
            update_search_images(searchJsonData)

        # Call the echo3D /search endpoint to get models and display the first 7 resulting thumbnails
        def on_click_search():
            searchTerm = searchInput.model.get_value_as_string()

            api_url = "https://api.echo3d.com/search"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
                "keywords": searchTerm,
                "include2Dcontent": "false"
            }

            librarySearchRequest = requests.post(url=api_url, data=data)
            global searchJsonData
            searchJsonData = librarySearchRequest.json()
            # searchLabel.text = "Showing results for: '" + searchTerm + "'"
            global search_image_widgets
            for i in range(IMAGES_PER_PAGE):
                if i < len(searchJsonData):
                    search_image_widgets[i].source_url = librarySearchRequest.json()[i]["thumbnail"]
                else:
                    search_image_widgets[i].source_url = ""

            # Filter the project assets to reflect the search
            global projectJsonData
            projectJsonData = [entry for entry in projectJsonData
                               if (entry["hologram"]["filename"].find(searchTerm) != -1)]
            
            global project_image_widgets
            for i in range(IMAGES_PER_PAGE):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    project_image_widgets[i].source_url = baseUrl + imageFilename
                else:
                    project_image_widgets[i].source_url = ""
  
        # Clear all the thumbnails
        def on_reset_search():
            searchInput.model.set_value("")
            global search_image_widgets
            for i in range(IMAGES_PER_PAGE):
                search_image_widgets[i].source_url = ""
            on_click_load_project()

        #################################################
        #     Define Functions for Project Querying     #
        #################################################

        # Load in new image thumbnails when clicks the previous/next buttons
        def update_project_images(projectJsonData):
            start_index = current_project_page * IMAGES_PER_PAGE
            end_index = start_index + IMAGES_PER_PAGE
            for i in range(start_index, end_index):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    project_image_widgets[i % IMAGES_PER_PAGE].source_url = baseUrl + imageFilename
                else:
                    project_image_widgets[i % IMAGES_PER_PAGE].source_url = ""

        def on_click_left_arrow_project():
            global current_project_page
            current_project_page -= 1
            global projectJsonData
            update_project_images(projectJsonData)

        def on_click_right_arrow_project():
            global current_project_page
            current_project_page += 1
            global projectJsonData
            update_project_images(projectJsonData)

        # Call the echo3D /query endpoint to get models and display the first 7 resulting thumbnails
        def on_click_load_project():
            api_url = "https://api.echo3d.com/query"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
            }

            projectQueryRequest = requests.post(url=api_url, data=data).json()["db"]
            values = list(projectQueryRequest.values())

            global projectJsonData
            projectJsonData = values
            global project_image_widgets
            for i in range(IMAGES_PER_PAGE):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    project_image_widgets[i].source_url = baseUrl + imageFilename
                else:
                    project_image_widgets[i].source_url = ""

        # Display the UI
        self._window = ui.Window("Echo3D", width=400, height=465)
        with self._window.frame:
            with ui.VStack():
                script_dir = os.path.dirname(os.path.abspath(__file__))
                image_filename = 'echo3D_Logo.png'
                image_path = os.path.join(script_dir, image_filename)
                with ui.Frame(height=25):
                    ui.Image(image_path)
                ui.Spacer(height=5)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    with ui.Frame(width=90):
                        ui.Label("API Key:")
                    apiKeyInput = ui.StringField()
                    ui.Spacer(width=5)
                ui.Spacer(height=3)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    with ui.Frame(width=90):
                        ui.Label("Security Key:")
                    secKeyInput = ui.StringField()
                    with ui.Frame(width=5):
                        ui.Label("")
                ui.Spacer(height=3)
                with ui.Frame(height=20):
                    ui.Button("Load Project", clicked_fn=on_click_load_project)
                ui.Spacer(height=3)
                with ui.HStack(height=5):
                    ui.Spacer(width=5)
                    ui.Line(name='default', style={"color": cl.gray})
                    ui.Spacer(width=5)
                ui.Spacer(height=3)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    ui.Label("Assets in Project:")

                apiKeyInput.model.set_value("summer-darkness-5935")
                secKeyInput.model.set_value("T8tbDSXApoJ1dQLnG0b3qPyY")
                global project_image_widgets
                with ui.HStack(height=80):
                    with ui.Frame(height=80, width=10):
                        ui.Button("<", clicked_fn=on_click_left_arrow_project)
                    ui.Spacer(width=5)
                    for i in range(IMAGES_PER_PAGE):
                        with ui.Frame(height=80):
                            project_image_widgets[i] = ui.Image("", fill_policy=ui.FillPolicy.PRESERVE_ASPECT_CROP,
                                                                alignment=ui.Alignment.CENTER,
                                                                style={'border_radius': 5})
                        ui.Spacer(width=5)
                    with ui.Frame(height=80, width=10):
                        ui.Button(">", clicked_fn=on_click_right_arrow_project)
                ui.Spacer(height=10)
                with ui.HStack(height=5):
                    ui.Spacer(width=5)
                    ui.Line(name='default', style={"color": cl.gray})
                    ui.Spacer(width=5)
                ui.Spacer(height=5)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    ui.Label("Public Search Results:")
                global search_image_widgets
                with ui.HStack(height=80):
                    with ui.Frame(width=10):
                        ui.Button("<", clicked_fn=on_click_left_arrow_search)
                    ui.Spacer(width=5)
                    for i in range(IMAGES_PER_PAGE):
                        search_image_widgets[i] = ui.Image("", fill_policy=ui.FillPolicy.PRESERVE_ASPECT_CROP,
                                                           alignment=ui.Alignment.CENTER,
                                                           style={'border_radius': 5})
                        ui.Spacer(width=5)
                    with ui.Frame(width=10):
                        ui.Button(">", clicked_fn=on_click_right_arrow_search)
                ui.Spacer(height=10)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    with ui.Frame(width=90):
                        ui.Label("Keywords:")
                    searchInput = ui.StringField()
                    searchInput.model.set_value("Dog")
                    with ui.Frame(width=5):
                        ui.Label("")
                ui.Spacer(height=5)
                with ui.VStack():
                    with ui.Frame(height=20):
                        ui.Button("Search", clicked_fn=on_click_search)
                    with ui.Frame(height=20):
                        ui.Button("Clear", clicked_fn=on_reset_search)

    def on_shutdown(self):
        print("[echo3D] echo3D shutdown")
