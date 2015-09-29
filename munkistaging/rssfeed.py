#
# This software is Copyright (c) 2015 University of Oxford
# 
# This work is made avaiable to you under the terms of the Apache
# License, Version 2.0; you may not use this source code except in
# compliance with the License. You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#

from PyRSS2Gen import RSS2,RSSItem, Guid

import datetime

class MunkiStagingRSSFeed(RSS2):

    def __init__(self,
                 title,
                 link,
                 description,

                 language = None,
                 copyright = None,
                 managingEditor = None,
                 webMaster = None,
                 pubDate = None,  # a datetime, *in* *GMT*
                 lastBuildDate = None, # a datetime
                 
                 categories = None, # list of strings or Category
                 generator = 'MunkiStagingRSSFeed 1.0',
                 docs = "https://docs.orchard.ox.ac.uk/rss",
                 cloud = None,    # a Cloud
                 ttl = None,      # integer number of minutes

                 image = None,     # an Image
                 rating = None,    # a string; I don't know how it's used
                 textInput = None, # a TextInput
                 skipHours = None, # a SkipHours with a list of integers
                 skipDays = None,  # a SkipDays with a list of strings

                 items = None,     # list of RSSItems
                 ):

        # Initialise base class .. 
        RSS2.__init__(self, title, link, description, language, copyright,
                 managingEditor, webMaster, pubDate, lastBuildDate,
                 categories, generator, docs, cloud, ttl, image,
                 rating, textInput, skipHours, skipDays, items)

        # Add media name space (for item icons)
        # Um ... rss_attrs is a class attribute, so this may have
        # unexpected side effects (but I don't particularly want to
        # re-engineer the class
        self.rss_attrs['xmlns:media'] = 'http://search.yahoo.com/mrss/'
        self.rss_attrs['xmlns:dc']    = 'http://purl.org/dc/elements/1.1/'

    def add_item(self, rss_item): 
        self.items.append(rss_item)
        

class MunkiStagingRSSItem(RSSItem):

    def __init__(self,
                 title = None,  # string
                 link = None,   # url as string
                 description = None, # string
                 author = None,      # email address as string
                 categories = None,  # list of string or Category
                 comments = None,  # url as string
                 enclosure = None, # an Enclosure
                 guid = None,    # a unique string
                 pubDate = None, # a datetime
                 source = None,  # a Source
                 icon_url = None,  # an icon to display
                 ):

        if guid is not None:
            guid = Guid(guid)

        # Initialise base class .. 
        RSSItem.__init__(self, title, link, description, author, categories,
                           comments, enclosure, guid, pubDate, source)

        # Add media name space (for item icons)
        self.icon = None
        if icon_url is not None:
            self.icon = MediaContentImage(icon_url)

    def publish_extensions(self, handler):
       if self.icon:
           self.icon.publish(handler)
       if self.pubDate and isinstance(self.pubDate, datetime.datetime):
           handler.startElement('dc:date', {})
           handler.characters( self.pubDate.strftime('%Y-%m-%dT%H:%M:%SZ') )
           handler.endElement('dc:date')

class MediaContentImage:
    """Publish an item Image
 
       Note that a media Content image can do so much more, but we
       focus on providing only what we need for Munki (i.e. providing
       an icon)
    """

    def __init__( self, url, type=None, isDefault='true',
                   height='300', width='300' ): # Height and width are
                                            # Munki recommended defaults

        self.name = 'media:content'
        self.element_attrs = {}

        self.element_attrs['url'] = url
        if type is not None:
            self.element_attrs['type'] = url

        self.element_attrs['isDefault'] = isDefault
        self.element_attrs['height'] = str(height) # Cast to be sure
        self.element_attrs['width'] = str(width) # Cast to be sure

    def publish(self, handler):
        handler.startElement(self.name, self.element_attrs)
        handler.endElement(self.name)
