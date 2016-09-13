#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This will display video and audio for the following meetings (as long as material is available)
# Akademy (structured by year, both audio and video available, slides are ignored)
# Randa Meetings (only video's available, no structure yet, slides are ignored)
# conf.kde.in (no audio or video available yet, slides are ignored)
import sys
import urlparse
import os.path

import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup
import requests


# Define the location where the audio and video is stored
# Note: this doesn't work with the http version because the mirroring system returns a different url each time you access a file
kde_files_scheme = "https"
kde_files_netloc = "files.kde.org" 
kde_files = "{scheme}://{netloc}".format(scheme=kde_files_scheme, netloc=kde_files_netloc)

LOCAL = 0
REMOTE = 1

# define the different directories, both their local name and their corresponding remote path 
akademy = "akademy"
randa = "randa"
confkdein = "confkdein"

addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'movies')
# check if we are in the root of the plugin
parsed_plugin_url = urlparse.urlparse(str(sys.argv[0]))
plugin_path = parsed_plugin_url.path
plugin_base = "{scheme}://{netloc}".format(scheme=parsed_plugin_url.scheme, netloc=parsed_plugin_url.netloc)

def get_base_items():
	# return only the items that should be shown in the root of the add-on
	return [
		("{base}/{item}{querystring}".format(base=plugin_base, item=akademy, querystring=str(sys.argv[2])), xbmcgui.ListItem(akademy), True),
		("{base}/{item}{querystring}".format(base=plugin_base, item=confkdein, querystring=str(sys.argv[2])), xbmcgui.ListItem(confkdein), True),
		("{base}/{item}{querystring}".format(base=plugin_base, item=randa, querystring=str(sys.argv[2])), xbmcgui.ListItem(randa), True)]

# Retrieve the items available at the current path
def get_dir_items_on_path():
	xbmc.log("path is {} with handle {} and qs {}".format(sys.argv[0], sys.argv[1], sys.argv[2]))
	retrieved_dir_items = list()
	remote_URL = "{}/{}".format(kde_files.rstrip("/"), plugin_path.lstrip("/"))
	index_page = BeautifulSoup(requests.get(remote_URL).text, "html.parser")
	for item in index_page.find_all("a"):
		# make sure the href doesn't refer to an external site
		parsed_item_URL = urlparse.urlparse(str(item["href"]))
		xbmc.log("Found remote URL: {}".format(remote_URL))
		xbmc.log("Found link: {}".format(parsed_item_URL.path))
		if not parsed_item_URL.netloc or parsed_item_URL.netloc == kde_files_netloc:
			# add the preceding part of the path, if it's a relative path
			abs_item_URL = str()
			if parsed_item_URL.path.startswith("/"):
				abs_item_URL = urlparse.urlunparse((kde_files_scheme, kde_files_netloc, parsed_item_URL.path, parsed_item_URL.params, parsed_item_URL.query, parsed_item_URL.fragment))
			else:
				abs_item_URL = "{}/{}".format(remote_URL.rstrip("/"), parsed_item_URL.path.lstrip("/"))
			parsed_abs_item_URL = urlparse.urlparse(abs_item_URL)
			# construct the absolute URL for this item
			xbmc.log("the absolute URL to this item is: {}".format(abs_item_URL))
			xbmc.log("the path from the absolute URL to this item is: {}".format(parsed_abs_item_URL.path))
			# make sure the URL refers to a deeper level than the current page
			if len(str(abs_item_URL)) > len(str(remote_URL)):
				# check if the path is a file or another directory
				path_parts = parsed_abs_item_URL.path.split("/")
				filename = path_parts[-1]
				directory = path_parts[-2]
				if filename: 
					# check the file type and add as link to file
					qs = urlparse.parse_qs(str(sys.argv[2]).lstrip("?"))
					accepted_formats = list()
					if "video" in qs["content_type"]:
						accepted_formats = xbmc.getSupportedMedia("video").split("|")
					elif "audio" in qs["content_type"]:
						accepted_formats = xbmc.getSupportedMedia("music").split("|")
					extension = os.path.splitext(parsed_abs_item_URL.path)[1]
					#xbmc.log("the extension is {} with acceptable formats: {}".format(extension, str(accepted_formats)))
					if extension in accepted_formats:
						retrieved_dir_items.append(("{file_URL}".format(file_URL=abs_item_URL), xbmcgui.ListItem(filename), False))
				else:
					retrieved_dir_items.append(("{base}/{path}{querystring}".format(base=plugin_base, path=parsed_abs_item_URL.path.lstrip("/"), querystring=str(sys.argv[2])), xbmcgui.ListItem(directory), True))
			
	
	return retrieved_dir_items

if not plugin_path:
	xbmc.log("Could not correctly detect the path in the add-on", xbmc.LOGERROR)
else:
	if plugin_path == "/":
		# add the directory items to Kodi
		if not xbmcplugin.addDirectoryItems(addon_handle, get_base_items()):
			xbmc.log("Could not create the directory listing in the add-on", xbmc.LOGERROR)
	else:
		# add the directory items to Kodi
		if not xbmcplugin.addDirectoryItems(addon_handle, get_dir_items_on_path()):
			xbmc.log("Could not create the directory listing in the add-on", xbmc.LOGERROR)
	# finish the directory listing
	xbmcplugin.endOfDirectory(addon_handle)
