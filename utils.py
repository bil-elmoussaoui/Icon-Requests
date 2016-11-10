from configparser import ConfigParser, NoOptionError
from os import listdir, path, getuid, environ as env, walk
from gi import require_version
from pwd import getpwuid
require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gio
from subprocess import Popen, PIPE
from collections import OrderedDict


def get_info_from_dsktp_file(desktop_file):
    config = ConfigParser()
    try:
        config.read(desktop_file)
        desktop_infos = {}
        try:
            desktop_infos["icon"] = config.get("Desktop Entry", "Icon")
            desktop_infos["is_hardcoded"] = is_hardcoded(desktop_infos["icon"])
            desktop_infos["is_supported"] = is_supported(
                desktop_infos["icon"], desktop_infos["is_hardcoded"])
            desktop_infos["name"] = config.get("Desktop Entry", "Name")
            desktop_infos["desktop"] = path.basename(desktop_file)
            desktop_infos[
                "path"] = "/".join(desktop_file.split("/")[:-1]) + "/"
            return desktop_infos
        except (KeyError, NoOptionError):
            return False
    except FileNotFoundError:
        return False


def get_theme_name():
    gsettings = Gio.Settings.new("org.gnome.desktop.interface")
    return str(gsettings.get_value("icon-theme")).strip("'")


def list_supported_icons():
    theme_name = get_theme_name()
    if theme_name.lower() in ["numix-square", "numix-circle"]:
        icons = []
        for icon_path in ICONS_PATHS:
            if path.exists(icon_path + theme_name):
                icons.extend(listdir(icon_path + theme_name + "/48/apps/"))
        icons = list(set(icons))
        icons = [icon.replace(".svg", "") for icon in icons]
        icons.sort()
        return icons
    else:
        pass
        return None

def is_gnome():
    """
        Check if the current distro is gnome
    """
    return env.get("XDG_CURRENT_DESKTOP").lower() == "gnome"


def get_user_destkop():
    p = Popen(["xdg-user-dir", "DESKTOP"], stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    return output.decode("utf-8").strip() + "/"


def get_username():
    return getpwuid(getuid())[0]

ICONS_PATHS = ["/usr/share/icons/",
               "/home/%s/.local/share/icons/" % get_username()]

DESKTOP_FILE_DIRS = ["/usr/share/applications/",
                     "/usr/share/applications/kde4/",
                     "/usr/local/share/applications/",
                     "/usr/local/share/applications/kde4/"
                     "/home/%s/.local/share/applications/" % get_username(),
                     "/home/%s/.local/share/applications/kde4/" % get_username(),
                     get_user_destkop()]

IGNORE_FILES = ["defaults.list", "mimeapps.list", "mimeinfo.cache"]

SUPPORTED_ICONS = list_supported_icons()

def is_hardcoded(icon_name):
    img_exts = ["png", "svg", "xpm"]
    icon_path = icon_name.split("/")
    ext = path.splitext(icon_name)[1]
    return len(icon_path) > 1 or ext.lower() in img_exts


def is_supported(icon_name, is_hardcoded):
    if is_hardcoded:
        icon_name = path.splitext(path.basename(icon_name))[0]
    return icon_name in SUPPORTED_ICONS


def get_desktop_files_info():
    global DESKTOP_FILE_DIRS, IGNORE_FILES
    desktop_files = {}
    for desktop_dir in DESKTOP_FILE_DIRS:
        if path.isdir(desktop_dir):
            all_files = listdir(desktop_dir)
            for desktop_file in all_files:
                desktop_file_path = desktop_dir + desktop_file
                ext = path.splitext(desktop_file)[1].lower().strip(".")
                if desktop_file and desktop_file not in IGNORE_FILES:
                    if ext == "desktop":
                        desktop_info = get_info_from_dsktp_file(
                            desktop_file_path)
                        if desktop_info:
                            desktop_files[desktop_file_path] = desktop_info
    data = OrderedDict(sorted(desktop_files.items(),
                              key=lambda x: x[1]["name"].lower()))
    return data


def get_icon(icon_name):
    """
        Generate a GdkPixbuf image
        :param image: icon name or image path
        :return: GdkPixbux Image
    """
    theme = Gtk.IconTheme.get_default()
    if is_hardcoded(icon_name):
        if path.isfile(icon_name):
            icon = GdkPixbuf.Pixbuf.new_from_file(icon_name)
        else:
            icon = theme.load_icon("image-missing", 48, 0)
    else:
        if theme.has_icon(icon_name):
            icon = theme.load_icon(icon_name, 48, 0)
        else:
            icon = theme.load_icon("image-missing", 48, 0)
    if icon.get_width() != 48 or icon.get_height() != 48:
        icon = icon.scale_simple(48, 48, GdkPixbuf.InterpType.BILINEAR)
    return icon

list_supported_icons()
