#
# Script to add
# * search domains
# * entry points for search domains
# to the webcrawler of elasticsearch's enterprise search tool.
#
# usage
#   python url_loader.py [-e http://user:password@elasticserverhost:9200] [-i .ent-search-actastic-crawler_domains_v2] [-u urlfile] [https://newdomain.org/somewhere]
#
# with
#   -e elasticserverhost    the url for an elasticsearch server that hosts enterprise search. Add user and password as required
#   -i crawler-index        the index name of the webcrawler list of searc domains. On v7.11 this is .ent-search-actastic-crawler_domains_v2
#   -u urlfile              a file contaning a list of domains and entry point urls, one line per entry, to be added
#   https://newdomain.org/somewhere is a new to be added domain (if a path is given, it will be added as such without adding /, this
#                           is useful e.g. when picking out a particular article off a site without having to worry about the landing
#                           page being indexed)
#
# Copyright (C) 2021 Klaus G. Paul for Arctic Basecamp Foundation
#
# Use at own risk. This script is based on undocumented functionality which may change without notice. Use is intended for educational
# or research purposes only. Not recommended to be used on an existing web crawler engine without having tested it on a separate engine
# first.
#
#
import click
import urllib
import requests
import json

class ENTSEARCHCRAWLER():
    """ENTSEARCHCRAWLER class

    Parameters:
    none for the class

    Class to provide basic CRU functionality to add urls to the Elasticsearch Enterprise Search Web Cralwer configuration.
    The missing Delete functionality is done best from the web frontend.

    """
    def __init__(self,elasticserver_url,searchengine_name=""):
        """init

        Parameters:
        elasticserver_url (str): url to an elastic search instance in the form http[s]://[<user>[:<password>]]@<host>[:<port>]/
        searchengine_name (str): name of the default search engine whose configuation is to be amended. Stored for subsequent use

        Returns:
        A new instance of class ENTSEARCHCRAWLER
        """
        elasticbits = urllib.parse.urlsplit(elasticserver_url)
        self.server_url = "{}://{}".format(elasticbits.scheme,elasticbits.netloc)
        
        r = requests.get(self.server_url+"/_cat/indices",headers={"Accept":"application/json"})
        retval = json.loads(r.text)
        self.crawler_index = ""
        self.search_engines_index = ""
        for entry in retval:
            if entry["index"] == ".ent-search-actastic-crawler_domains_v2":
                self.crawler_index = entry["index"]
            elif entry["index"] == ".ent-search-actastic-engines_v12":
                self.search_engines_index = entry["index"]
        if self.crawler_index == "":
            raise CrawlerDomainsNotFoundError("Could not find a crawler index on {}".format(self.server_url))
        if self.search_engines_index == "":
            raise SearchEnginesNotFoundError("Could not find a search engines on {}".format(self.server_url))
        
        self.engine = ""
        if searchengine_name != "":
            self.set_default_search_engine(searchengine_name)
        
        
    def get_search_engine_id_from_name(self,name):
        """get_search_engine_id_from_name

        Parameters:
        name (str): name of the search engine whose id is to be gathered

        Returns:
        id (str) if found, None if not
        """
        r = requests.get(self.server_url+"/"+self.search_engines_index+"/_search",json={"query":{"match": {"name": name}}},headers={"Accept":"application/json"})
        results = json.loads(r.text)
        results = results["hits"]["hits"]
        if len(results) > 0:
            if len(results) > 1:
                raise SearchEnginesMultipleNamesError("Multiple search engines with the same name '{}' on {}".format(name,self.server_url))
            for r in results:
                return r["_id"]
        else:
            return None
        
        
    def set_default_search_engine(self,name):
        """set_default_search_engine

        Set default search engine for subsequent operations, convenience function.

        Parameters:
        name (str): name of the search engine whose id is to be gathered

        Returns:
        ---
        """
        self.engine = self.get_search_engine_id_from_name(name)
        
    
    def create_new_id(self):
        """create_new_id

        Parameters:
        ---

        Returns:
        A valid id for Enterprise Search's web crawler (apparently this needs to be a 24 character hex number string) that does not yet exist.
        """
        for _ in range(9999):
            doc_id = str(uuid.uuid1()).replace("-","")[:24]
            r = requests.get(self.server_url+"/"+self.crawler_index+"/_doc/"+doc_id,headers={"Accept":"application/json"})
            retval = json.loads(r.text)
            if not retval["found"]:
                break
        else:
            raise CannotCreateUniqueIDError("Cannot create a unique ID, unknown reason, on {}".format(self.server_url))
        return doc_id    
        
        
    def check_if_domain_exists(self,domain,searchengine_name=""):
        """check_if_domain_exists
        """
        if searchengine_name != "":
            searchengine_id = self.get_search_engine_id_from_name(searchengine_name)
        elif self.engine != "":
            searchengine_id = self.engine
        else:
            searchengine_id = ""
        r = requests.get(self.server_url+"/"+self.crawler_index+"/_search",json={"query":{"match": {"name": domain}}},headers={"Accept":"application/json"})
        results = json.loads(r.text)
        results = results["hits"]["hits"]
        
        retval = 0
        for entry in results:
            if searchengine_id != "":
                if entry["_source"]["engine_oid"] == searchengine_id:
                    retval += 1
            else:
                retval += 1
        return retval


    def add_domain(self,domain,searchengine_name=""):
        """add_domain
        """
        parts = urllib.parse.urlsplit(domain)
        if self.check_if_domain_exists("{}://{}".format(parts.scheme,parts.hostname),searchengine_name=searchengine_name) > 0:
            # already exists
            pass
        if searchengine_name != "":
            searchengine_id = self.get_search_engine_id_from_name(searchengine_name)
        elif self.engine != "":
            searchengine_id = self.engine
        else:
            #searchengine_id = ""
            return {}
    
        doc_id = self.create_new_id()
        now = "{:%Y-%m-%dT%H:%M:%SZ}".format(datetime.datetime.utcnow())

        if parts.path == "": # no path give, use /
            seed_url = domain+"/"
        else:
            seed_url = domain
        
        document = {
            "id":doc_id,
            "created_at": now,
            "updated_at": now,
            "engine_oid": searchengine_id,
            "name": "{}://{}".format(parts.scheme,parts.hostname),
            "crawl_rules": [],
            "seed_urls":[
                {
                    "created_at":now,
                    "id":searchengine_id,
                    "url":seed_url #"{}://{}/".format(parts.scheme,parts.hostname)
                }
            ]
        }
    


        r = requests.put(self.server_url+"/"+self.crawler_index+"/_doc/"+id,json=document,headers={"Accept":"application/json"})
        result = json.loads(r.text)
        r = requests.post(self.server_url+"/"+self.crawler_index+"/_refresh",headers={"Accept":"application/json"})

        return result


    def update_seed_url_list(self,full_url,searchengine_name=""):
        """update_seed_url_list
        """
        parts = urllib.parse.urlsplit(full_url)
        if self.check_if_domain_exists("{}://{}".format(parts.scheme,parts.hostname),searchengine_name=searchengine_name) > 0:
            # already exists
            pass
        else:
            self.add_domain(full_url,searchengine_name=searchengine_name)
            
        if searchengine_name != "":
            searchengine_id = self.get_search_engine_id_from_name(searchengine_name)
        elif self.engine != "":
            searchengine_id = self.engine
        else:
            #searchengine_id = ""
            return {}
        
        query = {
            "query":{
                "bool": {
                    "must": [
                        {
                            "match": {
                                "name": {
                                    "query":parts.scheme+"://"+parts.hostname,
                                    "operator": "and"
                                }
                            }
                        },
                        {
                            "match": {
                                "engine_oid": {
                                    "query":searchengine_id,
                                    "operator": "and"
                                }
                            }
                        }
                    ]
                }
            }
        }
        r = requests.get(self.server_url+"/"+self.crawler_index+"/_search",json=query,headers={"Accept":"application/json"})
        result = json.loads(r.text)
        if len(result["hits"]["hits"]) == 1:
            document = result["hits"]["hits"][0]["_source"]
            doc_id = result["hits"]["hits"][0]["_id"]
        else:
            print("OOOPS")
            raise FoundMultipleDomainEntries("Multiple search engines with the same entry, specify the one you want on {}".format(self.server_url))
      

        now = "{:%Y-%m-%dT%H:%M:%SZ}".format(datetime.datetime.utcnow())


        if parts.path == "": # no path give, use /
            seed_url = full_url+"/"
        else:
            seed_url = full_url
            
        exists = False
        for s in document["seed_urls"]: # avoid duplicates
            if seed_url == s["url"]:
                exists = True
                break
                
        if not exists:
            print(document)
            new_seed = {
                "created_at": now,
                "id": searchengine_id,
                "url": seed_url
            }

            update = {
                "script": {
                    "source": "ctx._source.seed_urls.add(params.new_seed)",
                    "lang": "painless",
                    "params": {
                        "new_seed": new_seed
                    }
                }
            }
            print(update)
            print(self.server_url+"/"+self.crawler_index+"/_update/"+doc_id)

            r = requests.post(self.server_url+"/"+self.crawler_index+"/_update/"+doc_id,json=update)
            result = json.loads(r.text)
            print(result)
            r = requests.post(self.server_url+"/"+self.crawler_index+"/_refresh",headers={"Accept":"application/json"})
            
        return document


# TODO
# Integrate command line interface and class functionality

@click.command()
@click.option('--elasticserver', '-e', default="http://localhost:9200",help="url for elasticsearch",envvar="UL_ESERVER")
@click.option('--crawler_index', '-i', default=".ent-search-actastic-crawler_domains_v2",
    help="indexfile where enterprise search's web crawler stores urls",envvar="UL_CI")
@click.option('--urlfile', '-u',help="file with one url per line",type=click.File("rt"))
@click.argument('url',nargs=-1)
def main(elasticserver, crawler_index, url, urlfile):
    click.echo("{} {} {} {}".format(elasticserver, crawler_index, url, urlfile))

if __name__ == "__main__":
    main()