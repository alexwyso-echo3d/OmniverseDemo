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
project_image_widgets = [ui.Button() for _ in range(IMAGES_PER_PAGE)]
searchJsonData = []
projectJsonData = []
script_dir = os.path.dirname(os.path.abspath(__file__))
logo_image_filename = 'echo3D_Logo.png'
logo_image_path = os.path.join(script_dir, logo_image_filename)
cloud_image_filename = 'cloud_background_transparent.png'
cloud_image_path = os.path.join(script_dir, cloud_image_filename)
styles = [
    {
        "border_radius": 5,
        "Button.Image": {
            "color": cl("#FFFFFF"),
            "image_url": cloud_image_path,
            "alignment": ui.Alignment.CENTER
        }
    } for _ in range(IMAGES_PER_PAGE)]


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
            # global projectJsonData
            # projectJsonData = [entry for entry in projectJsonData
            #                    if (entry["hologram"]["filename"].find(searchTerm) != -1)]
            # global project_image_widgets
            # for i in range(IMAGES_PER_PAGE):
            #     if i < len(projectJsonData):
            #         baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
            #         imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
            #         project_image_widgets[i].source_url = baseUrl + imageFilename
            #     else:
            #         project_image_widgets[i].source_url = ""
  
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
                    styles[i % IMAGES_PER_PAGE] = {"Button.Image": {
                                        "color": cl("#FFFFFF"),
                                        "image_url": baseUrl + imageFilename,
                                        "alignment": ui.Alignment.CENTER,
                                        "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                                    },
                                    "border_radius": 5
                                    }
                    project_image_widgets[i % IMAGES_PER_PAGE].style = styles[i % IMAGES_PER_PAGE]
                    project_image_widgets[i % IMAGES_PER_PAGE].enabled = True
                else:
                    global cloud_image_path
                    styles[i % IMAGES_PER_PAGE] = {"Button.Image": {
                        "color": cl("#FFFFFF"),
                        "image_url": cloud_image_path,
                        "alignment": ui.Alignment.CENTER,
                        "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                    },
                    "border_radius": 5
                    }
                    project_image_widgets[i % IMAGES_PER_PAGE].style = styles[i % IMAGES_PER_PAGE]
                    project_image_widgets[i % IMAGES_PER_PAGE].enabled = False

        def on_click_left_arrow_project():
            global current_project_page
            current_project_page -= 1
            if (current_project_page == 0):
                projectLeftArrow.enabled = False
            projectRightArrow.enabled = True
            global projectJsonData
            update_project_images(projectJsonData)

        def on_click_right_arrow_project():
            global current_project_page
            current_project_page += 1
            global projectJsonData
            if ((current_project_page + 1) * IMAGES_PER_PAGE >= len(projectJsonData)):
                projectRightArrow.enabled = False
            projectLeftArrow.enabled = True
            update_project_images(projectJsonData)

        def on_click_project_image(index):
            global projectJsonData
            global current_project_page
            selectedEntry = projectJsonData[current_project_page * IMAGES_PER_PAGE + index]
            usdzStorageID = selectedEntry["additionalData"]["usdzHologramStorageID"]
            usdzFilename = selectedEntry["additionalData"]["usdzHologramStorageFilename"]

            if (usdzFilename):
                open_project_asset_from_filename(usdzFilename, usdzStorageID)
            else:
                glbStorageID = selectedEntry["hologram"]["storageID"]
                glbFilename = selectedEntry["hologram"]["filename"]
                open_project_asset_from_filename(glbFilename, glbStorageID)

        # Directly instantiate previously cached files from the session, or download them from the echo3D API
        def open_project_asset_from_filename(filename, storageId):
            folder_path = os.path.join(os.path.dirname(__file__), "temp_files")
            file_path = os.path.join(folder_path, filename)
            cachedUpload = os.path.exists(file_path)

            if (not cachedUpload):
                apiKey = apiKeyInput.model.get_value_as_string()
                secKey = secKeyInput.model.get_value_as_string()

                url = 'https://api.echo3d.com/query?key=' + apiKey + '&secKey=' + secKey + '&file=' + storageId

                response = requests.get(url)
                response.raise_for_status()

                with open(file_path, "wb") as file:
                    file.write(response.content)

            omni.kit.commands.execute('CreateReferenceCommand',
                                      path_to='/World/' + os.path.splitext(filename)[0],
                                      asset_path=file_path,
                                      usd_context=omni.usd.get_context())

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
            global styles
            for i in range(IMAGES_PER_PAGE):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    styles[i] = {
                        "Button.Image": {
                            "color": cl("#FFFFFF"),
                            "image_url": baseUrl + imageFilename,
                            "alignment": ui.Alignment.CENTER,
                            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                        },
                        "border_radius": 5
                    }
                    project_image_widgets[i].style = styles[i]
                    project_image_widgets[i].enabled = True
                    projectRightArrow.enabled = True
                else:
                    project_image_widgets[i].style = {}
                    project_image_widgets[i].enabled = False

        # Display the UI
        self._window = ui.Window("Echo3D", width=400, height=475)
        with self._window.frame:
            with ui.VStack():
                script_dir = os.path.dirname(os.path.abspath(__file__))
                logo_image_filename = 'echo3D_Logo.png'
                logo_image_path = os.path.join(script_dir, logo_image_filename)
                with ui.Frame(height=25):
                    ui.Image(logo_image_path)
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
                        projectLeftArrow = ui.Button("<", clicked_fn=on_click_left_arrow_project, enabled=False)
                    for i in range(IMAGES_PER_PAGE):
                        with ui.Frame(height=80):
                            project_image_widgets[i] = ui.Button("",
                                                                 clicked_fn=lambda index=i:
                                                                 on_click_project_image(index),
                                                                 style=styles[i], enabled=False)
                    with ui.Frame(height=80, width=10):
                        projectRightArrow = ui.Button(">", clicked_fn=on_click_right_arrow_project, enabled=False)
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
                                                           style={'border_radius': 5, 'border_width': 0})
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
        folder_path = os.path.join(os.path.dirname(__file__), "temp_files")

        # Get a list of all files in the temp folder
        file_list = os.listdir(folder_path)

        # Iterate over the file list and delete each file
        for file_name in file_list:
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print("[echo3D] echo3D shutdown")
