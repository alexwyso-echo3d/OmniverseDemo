import json
import os
import asyncio
import ssl
import certifi
import aiohttp
import omni.ext
import omni.ui as ui
import omni.kit.commands
import urllib
from omni.ui import color as cl

# GLOBAL VARIABLES #
IMAGES_PER_PAGE = 3
current_search_page = 0
current_project_page = 0
searchJsonData = []
projectJsonData = []

# UI Elements for the thumbnails
search_image_widgets = [ui.Image() for _ in range(IMAGES_PER_PAGE)]
project_image_widgets = [ui.Button() for _ in range(IMAGES_PER_PAGE)]

# Hardcoded echo3D images
script_dir = os.path.dirname(os.path.abspath(__file__))
logo_image_filename = 'echo3D_Logo.png'
logo_image_path = os.path.join(script_dir, logo_image_filename)
cloud_image_filename = 'cloud_background_transparent.png'
cloud_image_path = os.path.join(script_dir, cloud_image_filename)

# State variables to hold the style associated with each thumbnail
project_button_styles = [
    {
        "border_radius": 5,
        "Button.Image": {
            "color": cl("#FFFFFF30"),
            "image_url": cloud_image_path,
            "alignment": ui.Alignment.CENTER,
            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
        }
    } for _ in range(IMAGES_PER_PAGE)]
search_button_styles = [
    {
        "border_radius": 5,
        "Button.Image": {
            "color": cl("#FFFFFF30"),
            "image_url": cloud_image_path,
            "alignment": ui.Alignment.CENTER,
            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
        }
    } for _ in range(IMAGES_PER_PAGE)]

arrowStyle = {
    ":disabled": {
        "background_color": cl("#1f212460")
    },
    "Button.Label:disabled": {
        "color": cl("#FFFFFF40")
    }
}


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
            print(start_index)
            print(end_index)
            for i in range(start_index, end_index):
                if i < len(searchJsonData):
                    search_button_styles[i % IMAGES_PER_PAGE] = {"Button.Image": {
                                        "color": cl("#FFFFFF"),
                                        "image_url": searchJsonData[i]["thumbnail"],
                                        "alignment": ui.Alignment.CENTER,
                                        "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                                    },
                                    "border_radius": 5
                                    }
                    search_image_widgets[i % IMAGES_PER_PAGE].style = search_button_styles[i % IMAGES_PER_PAGE]
                    search_image_widgets[i % IMAGES_PER_PAGE].enabled = True
                else:
                    global cloud_image_path
                    search_button_styles[i % IMAGES_PER_PAGE] = {
                        "Button.Image": {
                            "color": cl("#FFFFFF30"),
                            "image_url": cloud_image_path,
                            "alignment": ui.Alignment.CENTER,
                            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                        },
                        "border_radius": 5
                    }
                    search_image_widgets[i % IMAGES_PER_PAGE].style = search_button_styles[i % IMAGES_PER_PAGE]
                    search_image_widgets[i % IMAGES_PER_PAGE].enabled = False

        # Update state variables to reflect change of page, disable arrow buttons, update the thumbnails shown
        def on_click_left_arrow_search():
            global current_search_page
            current_search_page -= 1
            if (current_search_page == 0):
                searchLeftArrow.enabled = False
            searchRightArrow.enabled = True
            global searchJsonData
            update_search_images(searchJsonData)

        def on_click_right_arrow_search():
            global current_search_page
            current_search_page += 1
            global searchJsonData
            if ((current_search_page + 1) * IMAGES_PER_PAGE >= len(searchJsonData)):
                searchRightArrow.enabled = False
            searchLeftArrow.enabled = True
            update_search_images(searchJsonData)

        async def on_click_search_image(index):
            global searchJsonData
            global current_search_page
            selectedEntry = searchJsonData[current_search_page * IMAGES_PER_PAGE + index]
            url = selectedEntry["glb_location_url"]
            filename = selectedEntry["name"] + '.glb'
            folder_path = os.path.join(os.path.dirname(__file__), "temp_files")
            file_path = os.path.join(folder_path, filename)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.read()

                    with open(file_path, "wb") as file:
                        file.write(content)

                    omni.kit.commands.execute('CreateReferenceCommand',
                                              path_to='/World/' + os.path.splitext(filename)[0].replace(" ", "_"),
                                              asset_path=file_path,
                                              usd_context=omni.usd.get_context())

                    api_url = "https://api.echo3d.com/upload"
                    data = {
                        "key": apiKeyInput.model.get_value_as_string(),
                        "secKey": secKeyInput.model.get_value_as_string(),
                        "data": "filePath:null",
                        "type": "upload",
                        "target_type": "2",
                        "hologram_type": "2",
                        "file_size": str(os.path.getsize(file_path)),
                        "file_model": open(file_path, "rb")
                    }

                    async with session.post(url=api_url, data=data) as uploadRequest:
                        uploadRequest.raise_for_status()
        
        # Call the echo3D /search endpoint to get models and display the resulting thumbnails
        def on_click_search():
            global current_search_page
            current_search_page = 0
            searchLeftArrow.enabled = False
            searchRightArrow.enabled = False
            searchTerm = searchInput.model.get_value_as_string()

            api_url = "https://api.echo3d.com/search"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
                "keywords": searchTerm,
                "include2Dcontent": "false"
            }

            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(api_url, data=encoded_data)
            response = urllib.request.urlopen(request, context=ssl.create_default_context(cafile=certifi.where()))
            librarySearchRequest = response.read().decode('utf-8')

            global searchJsonData
            searchJsonData = json.loads(librarySearchRequest)
            searchJsonData = [data for data in searchJsonData if "glb_location_url" in data
                              and data["source"] == 'poly']
            global search_image_widgets
            global search_button_styles
            for i in range(IMAGES_PER_PAGE):
                if i < len(searchJsonData):
                    search_button_styles[i] = {
                        "Button.Image": {
                            "color": cl("#FFFFFF"),
                            "image_url": searchJsonData[i]["thumbnail"],
                            "alignment": ui.Alignment.CENTER,
                            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                        },
                        "border_radius": 5
                    }
                    search_image_widgets[i].style = search_button_styles[i]
                    search_image_widgets[i].enabled = True
                    searchRightArrow.enabled = len(searchJsonData) > IMAGES_PER_PAGE
                else:
                    global cloud_image_path
                    search_button_styles[i] = {
                        "Button.Image": {
                            "color": cl("#FFFFFF30"),
                            "image_url": cloud_image_path,
                            "alignment": ui.Alignment.CENTER,
                            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                        },
                        "border_radius": 5
                    }
                    search_image_widgets[i].style = search_button_styles[i]
                    search_image_widgets[i].enabled = False
  
        # Clear all the thumbnails and search term
        def on_reset_search():
            global current_search_page
            current_search_page = 0
            searchInput.model.set_value("")
            global search_image_widgets
            for i in range(IMAGES_PER_PAGE):
                global cloud_image_path
                search_button_styles[i] = {
                    "Button.Image": {
                        "color": cl("#FFFFFF30"),
                        "image_url": cloud_image_path,
                        "alignment": ui.Alignment.CENTER,
                        "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                    },
                    "border_radius": 5
                }
                search_image_widgets[i].style = search_button_styles[i]
                search_image_widgets[i].enabled = False

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
                    project_button_styles[i % IMAGES_PER_PAGE] = {"Button.Image": {
                                        "color": cl("#FFFFFF"),
                                        "image_url": baseUrl + imageFilename,
                                        "alignment": ui.Alignment.CENTER,
                                        "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                                    },
                                    "border_radius": 5
                                    }
                    project_image_widgets[i % IMAGES_PER_PAGE].style = project_button_styles[i % IMAGES_PER_PAGE]
                    project_image_widgets[i % IMAGES_PER_PAGE].enabled = True
                else:
                    global cloud_image_path
                    project_button_styles[i % IMAGES_PER_PAGE] = {
                        "Button.Image": {
                            "color": cl("#FFFFFF30"),
                            "image_url": cloud_image_path,
                            "alignment": ui.Alignment.CENTER,
                            "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                        },
                        "border_radius": 5
                    }
                    project_image_widgets[i % IMAGES_PER_PAGE].style = project_button_styles[i % IMAGES_PER_PAGE]
                    project_image_widgets[i % IMAGES_PER_PAGE].enabled = False

        # Update state variables to reflect change of page, disable arrow buttons, update the thumbnails shown
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

        # When a user clicks a thumbnail, download the corresponding .usdz file if it exists and 
        # instantiate it in the scene. Otherwise use the .glb file
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
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            file_path = os.path.join(folder_path, filename)
            cachedUpload = os.path.exists(file_path)
            if (not cachedUpload):
                apiKey = apiKeyInput.model.get_value_as_string()
                secKey = secKeyInput.model.get_value_as_string()
                storageId = urllib.parse.quote(storageId)

                url = f'https://api.echo3d.com/query?key={apiKey}&secKey={secKey}&file={storageId}'

                response = urllib.request.urlopen(url, context=ssl.create_default_context(cafile=certifi.where()))

                response_data = response.read()

                with open(file_path, "wb") as file:
                    file.write(response_data)

            omni.kit.commands.execute('CreateReferenceCommand',
                                      path_to='/World/' + os.path.splitext(filename)[0],
                                      asset_path=file_path,
                                      usd_context=omni.usd.get_context())

        # Call the echo3D /query endpoint to get models and display the resulting thumbnails
        def on_click_load_project():
            global current_project_page
            current_project_page = 0
            projectLeftArrow.enabled = False
            projectRightArrow.enabled = False
            api_url = "https://api.echo3d.com/query"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
            }

            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(api_url, data=encoded_data)

            try:
                with urllib.request.urlopen(request,
                                            context=ssl.create_default_context(cafile=certifi.where())) as response:
                    response_data = response.read().decode('utf-8')
                    response_json = json.loads(response_data)
                    values = list(response_json["db"].values())
                    entriesWithScreenshot = [data for data in values if "additionalData" in data
                                             and "screenshotStorageID" in data["additionalData"]]
                    global projectJsonData
                    projectJsonData = entriesWithScreenshot
                    global project_image_widgets
                    global project_button_styles
                    
                    sampleModels = ["6af76ce2-2f57-4ed0-82d8-42652f0eddbe.png",
                                    "d2398ecf-566b-4fde-b8cb-46b2fd6add1d.png",
                                    "d686a655-e800-430d-bfd2-e38cdfb0c9e9.png"]

                    for i in range(IMAGES_PER_PAGE):
                        if i < len(projectJsonData):
                            imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                            if (imageFilename in sampleModels):
                                baseUrl = 'https://storage.echo3d.co/0_model_samples/'
                            else:
                                baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                            project_button_styles[i] = {
                                "Button.Image": {
                                    "color": cl("#FFFFFF"),
                                    "image_url": baseUrl + imageFilename,
                                    "alignment": ui.Alignment.CENTER,
                                    "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                                },
                                "border_radius": 5
                            }
                            project_image_widgets[i].style = project_button_styles[i]
                            project_image_widgets[i].enabled = True
                            projectRightArrow.enabled = len(projectJsonData) > IMAGES_PER_PAGE
                        else:
                            global cloud_image_path
                            project_button_styles[i] = {
                                "Button.Image": {
                                    "color": cl("#FFFFFF30"),
                                    "image_url": cloud_image_path,
                                    "alignment": ui.Alignment.CENTER,
                                    "fill_policy": ui.FillPolicy.PRESERVE_ASPECT_CROP
                                },
                                "border_radius": 5
                            }
                            project_image_widgets[i].style = project_button_styles[i]
                            project_image_widgets[i].enabled = False

                    searchButton.enabled = True
                    clearButton.enabled = True
                    searchInput.enabled = True
                    disabledStateCover.style = {"background_color": cl("#32343400")}
                    loadError.visible = False
            except Exception as e:
                loadError.visible = True
                print(str(e) + ". Ensure that your API Key and Security Key are entered correctly.")

        # Display the UI
        self._window = ui.Window("Echo3D", width=400, height=478)
        with self._window.frame:
            with ui.VStack():
                script_dir = os.path.dirname(os.path.abspath(__file__))
                logo_image_filename = 'echo3D_Logo.png'
                logo_image_path = os.path.join(script_dir, logo_image_filename)
                ui.Spacer(height=5)
                with ui.Frame(height=25):
                    ui.Image(logo_image_path)
                ui.Spacer(height=8)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    with ui.Frame(width=85):
                        ui.Label("API Key:")
                    apiKeyInput = ui.StringField()
                    ui.Spacer(width=5)
                ui.Spacer(height=3)
                with ui.HStack(height=20):
                    ui.Spacer(width=5)
                    with ui.Frame(width=85):
                        ui.Label("Security Key:")
                    secKeyInput = ui.StringField()
                    with ui.Frame(width=5):
                        ui.Label("")
                ui.Spacer(height=3)
                with ui.Frame(height=20):
                    ui.Button("Load Project", clicked_fn=on_click_load_project)
                loadError = ui.Label("Error: Cannot Load Project. Correct your keys and try again.", visible=False,
                                     height=20, style={"color": cl("#FF0000")}, alignment=ui.Alignment.CENTER)
                ui.Spacer(height=3)

                # Overlay the disabled elements to indicate their state
                with ui.ZStack():
                    with ui.VStack():
                        with ui.HStack(height=5):
                            ui.Spacer(width=5)
                            ui.Line(name='default', style={"color": cl.gray})
                            ui.Spacer(width=5)
                        ui.Spacer(height=3)
                        with ui.HStack(height=20):
                            ui.Spacer(width=5)
                            ui.Label("Assets in Project:")

                        global project_image_widgets
                        with ui.HStack(height=80):
                            with ui.Frame(height=80, width=10):
                                projectLeftArrow = ui.Button("<", clicked_fn=on_click_left_arrow_project, enabled=False,
                                                             style=arrowStyle)
                            for i in range(IMAGES_PER_PAGE):
                                with ui.Frame(height=80):
                                    project_image_widgets[i] = ui.Button("", clicked_fn=lambda index=i:
                                                                         on_click_project_image(index),
                                                                         style=project_button_styles[i], enabled=False)
                            with ui.Frame(height=80, width=10):
                                projectRightArrow = ui.Button(">", clicked_fn=on_click_right_arrow_project,
                                                              enabled=False, style=arrowStyle)
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
                            with ui.Frame(height=80, width=10):
                                searchLeftArrow = ui.Button("<", clicked_fn=on_click_left_arrow_search, enabled=False,
                                                            style=arrowStyle)
                            for i in range(IMAGES_PER_PAGE):
                                with ui.Frame(height=80):
                                    search_image_widgets[i] = ui.Button("",
                                                                        clicked_fn=lambda idx=i:
                                                                        asyncio.ensure_future(
                                                                            on_click_search_image(idx)),
                                                                        style=search_button_styles[i], enabled=False)
                            with ui.Frame(height=80, width=10):
                                searchRightArrow = ui.Button(">", clicked_fn=on_click_right_arrow_search, enabled=False,
                                                             style=arrowStyle)

                        ui.Spacer(height=10)
                        with ui.HStack(height=20):
                            ui.Spacer(width=5)
                            with ui.Frame(width=85):
                                ui.Label("Keywords:")
                            searchInput = ui.StringField(enabled=False)
                            with ui.Frame(width=5):
                                ui.Label("")
                        ui.Spacer(height=5)
                        with ui.VStack():
                            with ui.Frame(height=20):
                                searchButton = ui.Button("Search", clicked_fn=on_click_search, enabled=False)
                            with ui.Frame(height=20):
                                clearButton = ui.Button("Clear", clicked_fn=on_reset_search, enabled=False)

                    disabledStateCover = ui.Rectangle(style={"background_color": cl("#323434A0")}, height=500)

    def on_shutdown(self):
        # Clear all temporary download files
        folder_path = os.path.join(os.path.dirname(__file__), "temp_files")
        if os.path.exists(folder_path):
            file_list = os.listdir(folder_path)
            for file_name in file_list:
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        print("[echo3D] echo3D shutdown")
