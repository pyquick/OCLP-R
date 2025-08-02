import wx
import locale
import logging
import threading
import requests
from .. import (
    constants,
    sucatalog
)
from ..wx_gui import (
    gui_main_menu,
    gui_support,
    gui_download,
)
from ..support import (
    utilities,
    network_handler,
)
METALLIB_API_LINK_ORIGIN:     str  = "https://dortania.github.io/MetallibSupportPkg/manifest.json"
class MetallibDownloadFrame(wx.Frame):
    def __init__(self, parent: wx.Frame, title: str, global_constants: constants.Constants,screen_location: tuple = None):
        logging.info("Initializing NewMetallibDownloadFrame")
        self.constants: constants.Constants = global_constants
        self.title: str = title
        self.parent: wx.Frame = parent
        icon_path = str(self.constants.icns_resource_path / "Package.icns")
        self.icons = [self._icon_to_bitmap(icon_path), self._icon_to_bitmap(icon_path, (64, 64))]
        self.repl=False
        self.available_installers = None
        self.available_installers_latest = None
        self.backup_item=None
        self.kdk_data = None
        self.path_validate=None
        self.retry_download:bool=False
        self.show_fully=False
        self.kdk_data_full=None
        self.kdk_data_latest = None
        self.catalog_seed: sucatalog.SeedType = sucatalog.SeedType.DeveloperSeed
        self.frame_modal = wx.Dialog(parent, title=title, size=(330, 200))
        self.on_download()
    def _icon_to_bitmap(self, icon: str, size: tuple = (32, 32)) -> wx.Bitmap:
        return wx.Bitmap(wx.Bitmap(icon, wx.BITMAP_TYPE_ICON).ConvertToImage().Rescale(size[0], size[1], wx.IMAGE_QUALITY_HIGH))
    def _generate_catalog_frame(self) -> None:
        super(MetallibDownloadFrame, self).__init__(None, title=self.title, size=(300, 200), style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        gui_support.GenerateMenubar(self, self.constants).generate()
        self.Centre()
        title_label = wx.StaticText(self, label="Fetching Metallibs", pos=(-1,5))
        title_label.SetFont(gui_support.font_factory(19, wx.FONTWEIGHT_BOLD))
        title_label.Centre(wx.HORIZONTAL)
        progress_bar = wx.Gauge(self, range=100, pos=(-1, title_label.GetPosition()[1] + title_label.GetSize()[1] + 5), size=(250, 30))
        progress_bar.Centre(wx.HORIZONTAL)
        progress_bar_animation = gui_support.GaugePulseCallback(self.constants, progress_bar)
        progress_bar_animation.start_pulse()
        self.SetSize((-1, progress_bar.GetPosition()[1] + progress_bar.GetSize()[1] + 40))
        self.Show()
        def _fetch_installers():
            try:
                METALLIB_API_LINK: str = METALLIB_API_LINK_ORIGIN
                response = requests.get(METALLIB_API_LINK)
                self.kdk_data = response.json()
                self.kdk_data_latest = []
                kdk_data_number=[]
                kdk_data_build=[]
                maxnx=[]
                for i in range(len(self.kdk_data)):
                    data=self.kdk_data[i]["build"][:2]
                    data2=self.kdk_data[i]["build"]
                    kdk_data_number.append(data)
                    kdk_data_build.append(data2)
                for i in range(4):
                    try:
                        maxn=kdk_data_number[0]
                        while True:
                            kdk_data_number.pop(0)
                            if len(kdk_data_number)==0 or kdk_data_number[0]<maxn :
                                break
                        maxnx.append(maxn)
                    except:
                        break
                i=0
                fl=[0,0,0,0]
                while True:
                    if maxnx[0] == self.kdk_data[i]["build"][:2] and fl[0]==0:
                        self.kdk_data_latest.append(self.kdk_data[i])
                        fl[0]=1
                        i+=1
                    if len(maxnx)>=2:
                        if  maxnx[1] == self.kdk_data[i]["build"][:2]and fl[1]==0:
                            self.kdk_data_latest.append(self.kdk_data[i])
                            fl[1]=1
                            i+=1
                    if len(maxnx)>=3:
                        if  maxnx[2] == self.kdk_data[i]["build"][:2]and fl[2]==0:
                            self.kdk_data_latest.append(self.kdk_data[i])
                            fl[2]=1
                            i+=1
                    if len(maxnx)>=4:
                        if  maxnx[3] == self.kdk_data[i]["build"][:2]and fl[3]==0:
                            self.kdk_data_latest.append(self.kdk_data[i])
                            fl[3]=1
                            i+=1
                    if i==len(self.kdk_data)-1:
                        break
                    else:
                        i+=1
                        continue
                self.kdk_data_full=self.kdk_data
                self.kdk_data_latest=self.kdk_data_latest
            except requests.RequestException as e:
                wx.MessageBox(f"Fetch Metal Libraries Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
                self.on_return_to_main_menu()
        thread = threading.Thread(target=_fetch_installers)
        thread.start()
        gui_support.wait_for_thread(thread)
        progress_bar_animation.stop_pulse()
        progress_bar.Hide()
        self._display_available_installers()
    def convert_size(self,size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    def detect_os_build(self, rsr: bool = False) -> str:
        import plistlib
        file_path = "/System/Library/CoreServices/SystemVersion.plist"
        if rsr is True:
            file_path = f"/System/Volumes/Preboot/Cryptexes/OS{file_path}"

        try:
            return plistlib.load(open(file_path, "rb"))["ProductBuildVersion"]
        except Exception as e:
            raise RuntimeError(f"Failed to detect OS build: {e}")
    def _display_available_installers(self, event: wx.Event = None, show_full: bool = False) -> None:
        self.os_build_tahoe=self.detect_os_build(False)
        bundles = [wx.BitmapBundle.FromBitmaps(self.icons)]
        self.frame_modal.Destroy()
        self.frame_modal = wx.Dialog(self, title="Choose Metallib Version", size=(420, 580))
        title_label = wx.StaticText(self.frame_modal, label="Choose Metallib", pos=(-1,-1))
        title_label.SetFont(gui_support.font_factory(19, wx.FONTWEIGHT_BOLD))
        id = wx.NewIdRef()
        self.list = wx.ListCtrl(self.frame_modal, id, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.BORDER_SUNKEN)
        self.list.SetSmallImages(bundles)
        self.list.InsertColumn(0, "name",        width=160)
        self.list.InsertColumn(1, "version",      width=50)
        self.list.InsertColumn(2, "build",        width=75)
        self.list.InsertColumn(3, "seen", width=105)
        if show_full is False:
            self.frame_modal.SetSize((420, 320))
        installers = self.kdk_data_latest[::-1] if show_full is False else self.kdk_data_full[::-1]
        if installers:
            import re
            locale.setlocale(locale.LC_TIME, '')
            logging.info(f"Available installers on Github ({'All entries' if show_full else 'Latest only'}):")
            xnu_name={
                "26":"Tahoe Beta",
                "15":"Sequoia",
                "14":"Sonoma",
                "13":"Ventura",
            }
            for item in installers:
                logging.info(f"- {item['name']} (macOS {item['version']} - {item['build']}):\n   - Link: {item['url']}\n")
                result = re.search(r'^\d+', item['version'])
                index = self.list.InsertItem(self.list.GetItemCount(), f"macOS {xnu_name[result.group()]}")
                self.list.SetItemImage(index, 0)
                self.list.SetItem(index, 1, f"{item['version']}")
                self.list.SetItem(index, 2, f"{item['build']}")
                self.list.SetItem(index, 3, f"{item['seen']}")
        else:
            logging.error("Cannot find any installers on Dortania")
            wx.MessageDialog(self.frame_modal, "Failed to download Metallib message from Github", "Error", wx.OK | wx.ICON_ERROR).ShowModal()
            self.on_return_to_main_menu()
        if show_full is False:
            self.list.Select(-1)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_select_list)
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_list)
        self.select_button = wx.Button(self.frame_modal, label="Download", pos=(-1, -1), size=(150, -1))
        self.select_button.SetFont(gui_support.font_factory(13, wx.FONTWEIGHT_NORMAL))
        self.select_button.Bind(wx.EVT_BUTTON, lambda event, installers=installers: self.on_download_installer(installers))
        self.select_button.SetToolTip("Download Selected Metallib")
        self.select_button.SetDefault()
        if show_full is True:
            self.select_button.Disable()
        self.copy_button = wx.Button(self.frame_modal, label="Copy Link", pos=(-1, -1), size=(80, -1))
        self.copy_button.SetFont(gui_support.font_factory(13, wx.FONTWEIGHT_NORMAL))
        if show_full is True:
            self.copy_button.Disable()
        self.copy_button.SetToolTip("Copy Metallib Download Link")
        self.copy_button.Bind(wx.EVT_BUTTON, lambda event, installers=installers: self.on_copy_link(installers))
        return_button = wx.Button(self.frame_modal, label="Return to Main Menu", pos=(-1, -1), size=(150, -1))
        return_button.Bind(wx.EVT_BUTTON, self.on_return_to_main_menu)
        return_button.SetFont(gui_support.font_factory(13, wx.FONTWEIGHT_NORMAL))
        self.showolderversions_checkbox = wx.CheckBox(self.frame_modal, label="Show Older/Beta Version", pos=(-1, -1))
        if show_full is True:
            self.showolderversions_checkbox.SetValue(True)
        self.showolderversions_checkbox.Bind(wx.EVT_CHECKBOX, lambda event: self._display_available_installers(event, self.showolderversions_checkbox.GetValue()))
        if self.os_build_tahoe!='25A5316i':
            rectbox = wx.StaticBox(self.frame_modal, -1)
            rectsizer = wx.StaticBoxSizer(rectbox, wx.HORIZONTAL)
            rectsizer.Add(self.copy_button, 0, wx.EXPAND | wx.RIGHT, 5)
            rectsizer.Add(self.select_button, 0, wx.EXPAND | wx.LEFT, 5)
        checkboxsizer = wx.BoxSizer(wx.HORIZONTAL)
        checkboxsizer.Add(self.showolderversions_checkbox, 0, wx.ALIGN_CENTRE | wx.RIGHT, 5)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        sizer.Add(title_label, 0, wx.ALIGN_CENTRE | wx.ALL, 0)
        sizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 10)
        if self.os_build_tahoe!='25A5316i':
             sizer.Add(rectsizer, 0, wx.ALIGN_CENTRE | wx.ALL, 0)
             sizer.AddSpacer(8)
        elif self.os_build_tahoe=='25A5316i':
            mosizer=wx.BoxSizer(wx.HORIZONTAL)
            mosizer.Add(self.copy_button, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
            mosizer.Add(self.select_button, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
            sizer.Add(mosizer, 0, wx.ALIGN_CENTRE | wx.ALL, 0)
            sizer.AddSpacer(8)
        sizer.Add(checkboxsizer, 0, wx.ALIGN_CENTRE | wx.ALL, 15)
        sizer.Add(return_button, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 15)
        self.frame_modal.SetSizer(sizer)
        self.frame_modal.ShowWindowModal()
    def on_copy_link(self, installers: dict) -> None:
        selected_item = self.list.GetFirstSelected()
        if selected_item != -1:
            clipboard = wx.Clipboard.Get()
            if not clipboard.IsOpened():
                clipboard.Open()
            clipboard.SetData(wx.TextDataObject(installers[selected_item]['url']))
            clipboard.Close()
            wx.MessageDialog(self.frame_modal, "", "", wx.OK | wx.ICON_INFORMATION).ShowModal()
    def on_select_list(self, event):
        if self.list.GetSelectedItemCount() > 0:
            self.select_button.Enable()
            self.copy_button.Enable()
        else:
            self.select_button.Disable()
            self.copy_button.Disable()   
    def on_download_installer(self, installers: dict) -> None:
        selected_item = self.list.GetFirstSelected()
        if selected_item != -1:
            selected_installer = installers[selected_item]
            while True:
                dir_dialog = wx.DirDialog(self, "Select Save Path", "", wx.DD_DIR_MUST_EXIST)
                if dir_dialog.ShowModal() == wx.ID_OK:
                    save_path = dir_dialog.GetPath()
                    def is_dir_writable(dirpath):
                        import os
                        return os.access(dirpath, os.W_OK | os.X_OK)
                    if not is_dir_writable(save_path):
                        wx.MessageBox(
                            "Cannot write to the selected directory.", 
                            "Read_only directory", 
                            wx.OK | wx.ICON_WARNING
                        )  
                        dir_dialog.Destroy()
                    else:
                        logging.info(f"Selected Path: {save_path}")
                        dir_dialog.Destroy()
                        break
                else:
                    self.on_return_to_main_menu()
                    return
                
            file_name = selected_installer['name']+".pkg"
            self.frame_modal.Close()
            download_obj = network_handler.DownloadObject(selected_installer['url'], save_path+"/"+file_name)
          
            gui_download.DownloadFrame(
                self,
                title=self.title,
                global_constants=self.constants,
                download_obj=download_obj,
                item_name=f"Metallib {selected_installer['version']} {selected_installer['build']}",
                download_icon=str(self.constants.icns_resource_path / "Package.icns")
            )
            if download_obj.download_complete is False:
                import os
                os.remove(save_path+"/"+file_name)
                self.on_return_to_main_menu()
                return
            
            self.on_return_to_main_menu()
    def on_download(self) -> None:
        self.frame_modal.Close()
        self.parent.Hide()
        self._generate_catalog_frame()
        self.parent.Close()

    def on_return_to_main_menu(self, event: wx.Event = None) -> None:
       
        if self.frame_modal:
            self.frame_modal.Hide()
        main_menu_frame = gui_main_menu.MainFrame(
            None,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetScreenPosition()
        )
        main_menu_frame.Show()
        if self.frame_modal:
            self.frame_modal.Destroy()
        self.Destroy()
    