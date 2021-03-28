# Enterprise Search Web Crawler domain and url uploader

Script to add
* search domains
* entry points for search domains
to the webcrawler of elasticsearch's enterprise search tool.

## Usage

`python url_loader.py [-e http://user:password@elasticserverhost:9200] [-i .ent-search-actastic-crawler_domains_v2] [-u urlfile] [https://newdomain.org/somewhere]`

with

-e elasticserverhost    the url for an elasticsearch server that hosts enterprise search. Add user and password as required

-i crawler-index        the index name of the webcrawler list of searc domains. On v7.11 this is .ent-search-actastic-crawler_domains_v2

-u urlfile              a file contaning a list of domains and entry point urls, one line per entry, to be added

https://newdomain.org/somewhere is a new to be added domain (if a path is given, it will be added as such without adding /, this
                           is useful e.g. when picking out a particular article off a site without having to worry about the landing
                           page being indexed)


*This script is incomplete and has bugs, be patient*

