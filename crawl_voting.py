#! /usr/bin/python
# -*- coding: utf-8 -*-
from urllib import urlopen

# Fetch source HTML of specified page
# Return: Page source, or exit if exception.
def get_page(url):
        try:
                page = urlopen(url).read()
                return page

        except Exception, err:
                print "Fail to get the page: " + str(err)

# Find all tag ... endtag
# Return: A list with text in specified tag
def find_tag_text(instr, tag, endtag):
        from re import search
        
        resultList = []
        curPos = 0
        while True:
                target_tag = search(tag, instr[curPos:])
                if target_tag == None:
                        break
                target_tag = target_tag.group(0)
                curPos = instr.find(target_tag, curPos)
                
                target_end_tag = search(endtag, instr[curPos:])
                if target_end_tag == None:
                        resultList.append(instr[curPos + len(tag):len(instr) - 1])
                        break
                target_end_tag = target_end_tag.group(0)
                endPos = instr.find(target_end_tag, curPos)
                resultList.append(instr[curPos + len(target_tag):endPos])

                curPos = endPos + 1
        
        return resultList
       
# Fetch page source and crawl url list.
# Rule: <td nowrap rowspan=(\d+) align=center><a href=(CRAWL_THIS_LINK)>TEXT</td>
def fetch_url_list(page_url, domain, level, rest_level):

        page_content = get_page(page_url)
        area_list = find_tag_text(page_content, '<td nowrap rowspan=\d+ align=center>', "</td>")
        url_list = []
        for area in area_list:
                url = find_tag_text(area, '<a href="', '">')
                url_list.append(domain + url[0])

        if rest_level - 1 == 0:
                return url_list
        else:
                deeper_list = []
                for url in url_list:
                        if level[len(level) - rest_level + 1] == "left_link":
                                deeper_list += fetch_url_list(url, domain, level, rest_level - 1)
                        else:
                                deeper_list += fetch_all_url_list(url, domain, level, rest_level - 1)
                return deeper_list

# Fetch page source and crawl url list.
# Rule: <table>... CRAWL_ALL_LINKS ...</table>
def fetch_all_url_list(page_url, domain, level, rest_level):

        page_content = get_page(page_url)
        area_list = find_tag_text(page_content, '<table ', "</table>")
        sub_url_list = find_tag_text(area_list[0], '<a href="', '">')
        url_list = [domain + url for url in sub_url_list]

        if rest_level - 1 == 0:
                return url_list
        else:
                deeper_list = []
                for url in url_list:
                        if level[len(level) - rest_level + 1] == "left_link":
                                deeper_list += fetch_url_list(url, domain, level, rest_level - 1)
                        else:
                                deeper_list += fetch_all_url_list(url, domain, level, rest_level - 1)
                return deeper_list

# Fetch voting rate from page source.
def fetch_voting_rate(url_list, filename):
        done = 0
        
        with open(filename, 'a') as f:
                for url in url_list:
                        print("Fetching: " + url + " ... "),
                        for i in range(2): # Avoid Bad Getway, try to crawl page twice
                                page_content = get_page(url) 
                                table_content = find_tag_text(page_content, "<table .*?>", "</table>")
                                if len(table_content) < 1:
                                        print "Failed."
                                else:
                                        f.write('<table>')

                                        # Remove title
                                        table_content = table_content[0]
                                        pos = table_content.find('<tr class="title">')
                                        table_content = table_content[pos + 18:]
                                        while table_content.find('<tr class="title">') != -1:
                                                table_content = table_content[table_content.find('<tr class="title">') + 18:]
                                        content = table_content[table_content.find('</tr>') + 5:]
                                        
                                        f.write(str(content))
                                        f.write('</table>')
                                        print "Successed."
                                        done += 1
                                        break
        print "Finish fetching: " + str(done) + " / " + str(len(url_list))
        return

if __name__ == "__main__":
        from time import ctime
        from time import time
        import sys
        domain = ""
        page = ""
        record_name = ""
        level = []
        mode = 0

        with open("config.txt", "r") as f:
                try:
                        import re
                        for line in f:
                                rline = line.replace("\n", "")
                                if re.search("Domain:\s*", rline):
                                        pts = (re.search("Domain:\s*", rline)).group(0)
                                        domain = rline[rline.find(pts) + len(pts):]
                                        print "Domain: " + str(domain)
                                elif re.search("Seek_page:\s*", rline):
                                        pts = (re.search("Seek_page:\s*", rline)).group(0)
                                        page = rline[rline.find(pts) + len(pts):]
                                        print "Seek_page: " + str(page)
                                elif re.search("Save_as:\s*", rline):
                                        pts = (re.search("Save_as:\s*", rline)).group(0)
                                        record_name = rline[rline.find(pts) + len(pts):]
                                        print "Save as: " + str(record_name)
                                elif re.search("Level\s*\d+:\s*", rline):
                                        pts = (re.search("Level\s*", rline)).group(0)
                                        lv = int(rline[rline.find(pts) + len(pts):rline.find(":")])
                                        pts = (re.search("Level\s*\d+:\s*", rline)).group(0)
                                        m = rline[rline.find(pts) + len(pts):]
                                        if m != "null":
                                                level.append([lv, m])

                        level = sorted(level, key = lambda x : x[0])
                        level = [lv[1] for lv in level]
                        for i in range(len(level)):
                                print "Level " + str(i + 1) + ": " +  str(level[i])
                        print "Config setting done."

                except Exception, err:
                        print "Fail to setup config file: " + str(err)

        startTime = time()
        print "Program start at " + ctime()
                
        print "Fetching url list..."
        if level[0] == "left_link":
                print "Mode 0: According to the links on the first column of seek page."
                url_list = fetch_url_list(page, domain, level, len(level))
        else:
                print "Mode 1: According to all links on the table of seek page."
                url_list = fetch_all_url_list(page, domain, level, len(level))

        print "Fetching data..."
        fetch_voting_rate(url_list, record_name)
        print "Done. Execution time: " + str(time() - startTime)

