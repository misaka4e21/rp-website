#!/usr/bin/env python2
#coding: utf-8
from __future__ import print_function

import json

import os
import sys
import datetime
import hashlib

fconf = open('config.json','r+')
config = json.load(fconf)
fconf.close()

try:
    unicode=unicode
    reload(sys)
    sys.setdefaultencoding('UTF8')
except:
    unicode=str

def banner_tag(params):
    img_url = params.split(" ")[0]
    caption = " ".join(params.split(" ")[1:])
    # Add <span> tags if there's a provided caption.
    span_caption = '<span class="caption">%s</span>' % caption if caption else ""
    return """<div class="img-wrap post-banner"><img src="%s" class="border" alt="%s">%s</div>""" % (img_url, caption, span_caption)
    
def _cfg(key, config=config, lang='en'):
    # Get config value. lang->fallback->'global'
    fallback = config['global'].get('fallback', 'en')
    cfg_lang = config[lang]
    cfg_fallback = config.get(fallback)
    value = cfg_lang.get(key)
    if value == None and cfg_fallback != None:
        value = cfg_fallback.get(key)
    if value == None:
        value = config['global'].get(key)
    return value

def article_filename(idx):
    filename = str(idx)
    filename = "0" * (4 - len(filename)) + filename
    return filename
    
class Interface:
    def c(self, key,default=None):
        r=_cfg(key,lang=self.lang)
        if r==None:
            r=default
        return r

    def __init__(self, lang='en'):
        self.lang = lang
        self.build_prefix = self.c('build_prefix')
        self.data_prefix = self.c('data_prefix')
        self.link_prefix = self.c('link_prefix')
        self.articles_prefix = self.c('articles_prefix')
        # Must end in a /
        assert self.link_prefix[-1] == "/", "Must end in a /"
        self.params = {
            "title": self.c('title'),
            "data_prefix": self.data_prefix,
            "prefix": self.link_prefix,
            "res_prefix": self.link_prefix+'resources/',
        }

    def _filter(self, page, user_params):
        params = self.params.copy()
        params.update(user_params)
        page = unicode(page)
        for name, value in params.items():
            var_name = "${%s}" % name
            page = page.replace(var_name, unicode(value))
        return page

    def get_articles_dir(self):
        return self.data_prefix + self.articles_prefix

    def link(self, url):
        return self.link_prefix + url

    def template(self, name, user_params={}):
        return self._filter(open(os.path.join(self.data_prefix,"templates",name),'r',).read(), user_params)

    def write(self, pagename, page):
        open(self.build_prefix + pagename, "w",).write(page)

    def raw_article(self, idx, user_params={}):
        filename = os.path.join(self.get_articles_dir(), article_filename(idx))
        return self._filter(open(filename,'r').read(), user_params)

    def mkdir_p(self, path):
        path = self.build_prefix + path
        if not os.path.exists(path):
            os.makedirs(path)

class Generator(Interface):

    def generate(self):
        self.categories = self.c('categories')
        self.mkdir_p("category/")
        self.mkdir_p("archive/")
        self.generate_index_html()
        self.build_gallery("rojavaplan")
        for page_name in self.c('main_pages'):
            self.build_main_page(page_name)
        self.generate_news_html()
        self.generate_full_archive()

        for category_name in self.c('categories').keys():
            self.generate_category_html(category_name, 8)

        self.generate_archive_html(datetime.date(2015, 11, 1))
        for i in range(self.get_highest_index()):
            self.generate_article(i + 1)

    def get_highest_index(self):
        highest_idx = 0
        for filename in os.listdir(self.get_articles_dir()):
            try:
                idx = int(filename)
            except ValueError:
                pass
            else:
                if idx > highest_idx:
                    highest_idx = idx
        return highest_idx
    
   
    def disqus_data(self,article):
        link = self.c('base_url') + \
            self.link(self.article_output_filename(article))
        ident = hashlib.md5(link.encode('utf-8')).hexdigest()
        return link, ident
    
    def parse_article(self, idx):
        def translate_category(category):
            mappings = self.c('mappings',default={})
            if category not in mappings.keys():
                return category
            return mappings[category]

        try:
            raw = self.raw_article(idx)
        except IOError:
            return None
        sections = raw.split("---\n")
        assert(len(sections) == 3)
        title_data = tuple(sections[0].split("\n")[:-1])
        assert(len(title_data) in [4,5])
        date = datetime.datetime.strptime(title_data[1], "%b %d, %Y")
        categories = [category.strip() for category in title_data[3].split(",")]
        # Translate them to foreign language if needed
        categories = [translate_category(category) for category in categories]
        return {
            "title": title_data[0],
            "date": date,
            "preview": title_data[2],
            "categories": categories,
            "blurb": sections[1],
            "main": sections[2]
        }
    
    def generate_index_html(self):
        html_header = self.template("header.html")
        html_footer = self.template("footer.html")
    
        html_index_content_header = self.template("index-content-header.html")
        output_page = html_header + html_index_content_header
        current_idx = self.get_highest_index()
    
        for i in range(4):
            article = self.parse_article(current_idx)
            if not article:
                break
            link = self.link(self.article_output_filename(article))
            date_formatted = article["date"].strftime("%b %d, %Y")
            output_page += """
            <article>
                <a href="%s"><img src="%s" class="border" alt="image">
                <h1>%s</h1></a>
                <p>%s</p>
                <p class="meta"><time pubdate="">%s</time> / <a href="%s">{read}</a></p>
            </article>
            """.format(**self.c('l10n')) % (link, article["preview"], article["title"], article["blurb"],
                   date_formatted, link)
            current_idx -= 1
    
        output_page += """
    
    <div id="pagination">
    	<span class="hide">|</span> 
    	<a href="%s" class="button older">{older_entries}</a>
    </div>
    
    </section><!-- /#main -->
    
    </div><!-- /#content -->
    
    """.format(**self.c('l10n')) % self.link("fullarchive.html")
    
        output_page += html_footer
    
        self.write("index.html", output_page)
    
    def build_gallery(self, name):
        html_header = self.template("header.html")
        html_footer = self.template("footer.html")
    
        html_page_content = self.template("%s-content.html" % name)
        output_page = html_header
        output_page += '<div id="content" class="gallery">\n'
        output_page += html_page_content
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.write("%s.html" % name, output_page)
    
    def build_main_page(self, name):
        html_header = self.template("header.html")
        html_footer = self.template("footer.html")
    
        html_page_content = self.template("%s-content.html" % name)
        html_mainpages_content_footer = self.template("mainpages-content-footer.html")
        output_page = html_header
        output_page += '<div id="content" class="page">\n'
        output_page += html_page_content
        output_page += html_mainpages_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.write("%s.html" % name, output_page)
    
    def article_output_path(self,article):
        return "articles/%s/%s/" % (
            article["date"].year, article["date"].month)
    
    def article_output_filename(self,article):
        filename = article["title"].replace(" ", "-")
        filename = filename.replace("?", "").replace("!", "").replace(".", "")
        filename = filename.lower()
        return "%s%s.html" % (self.article_output_path(article), filename)
    
    def build_article_item(self, article):
        link = self.link(self.article_output_filename(article))
        disqus_link, ident = self.disqus_data(article)
        item = """
    <article>
    
    	<header>
    		<h1><a href="%s">%s</a></h1>
    	</header>
    		
    	<div class="group">
    		<div class="img-wrap post-image"><img src="%s" class="border" alt="image"></div>
            <p>%s</p>
    		<p><a href="%s">{continue_reading}</a></p>
        </div>
    
    	<footer>
    		<ul>
    			<li class="date"><time datetime="2012-05-17T08:35-05:00" pubdate=""><span>%s</span> <em>%s</em></time></li>
    			<li class="comments"><a href="%s#disqus_thread" data-disqus-identifier="%s">Leave a comment</a></li>
    			<li class="tags">
    """ .format(**self.c('l10n')) % (link, article["title"], article["preview"], article["blurb"], link,
           article["date"].year, article["date"].strftime("%b %d"),
           link, ident)
    
        for category in article["categories"]:
            try:
                category_handle = self.categories[category]
            except KeyError:
                print("************************************************",file=sys.stderr)
                print("Error: Non existant category: %s" % category,file=sys.stderr)
                print("************************************************",file=sys.stderr)
                raise Exception("Non existant category: %s" % category)
            category_link = self.link("category/%s.html" % category_handle)
            item += '<a href="%s">%s</a> ' % (category_link, category)
    
        item += """
                </li>
    		</ul>
    	</footer>
    		
    </article>
    """
        return item
    
    def generate_news_html(self):
        html_header = self.template("header.html")
        html_article_content_footer = self.template("article-content-footer.html")
        html_footer = self.template("footer.html")
    
        output_page = html_header
        output_page += """
    <div id="content" class="blog post multiple">
    
    <header role="page">
        <h1 class="blog icon">{news}</h1>
    	<p>{news_content}</p1>
    </header>
    	
    <section id="main">
    
    """.format(**self.c('l10n')) 
    
        current_idx = self.get_highest_index()
    
        for i in range(4):
            article = self.parse_article(current_idx)
            if not article:
                break
            output_page += self.build_article_item(article)
            current_idx -= 1
    
        output_page += """
    
    <div id="pagination">
    	<span class="hide">|</span> 
    	<a href="%s" class="button older">{older_entries}</a>
    </div>
    
    </section><!-- /#main -->
    
    """.format(**self.c('l10n')) % self.link("fullarchive.html")
    
        output_page += html_article_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.write("news.html", output_page)
    
    def generate_category_html(self, indexed_category, limit):
        html_header = self.template("header.html")
        html_article_content_footer = self.template("article-content-footer.html")
        html_footer = self.template("footer.html")
    
        output_page = html_header
        output_page += """
    <div id="content" class="blog post multiple">
    
    <header role="page">
        <h1>%s</h1>
    	<p>{tagged} "%s".</p1>
    </header>
    	
    <section id="main">
    
    """.format(**self.c('l10n')) % (indexed_category, indexed_category)
    
        current_idx = self.get_highest_index()
    
        for i in range(self.get_highest_index()):
            article = self.parse_article(current_idx)
    
            if indexed_category not in article["categories"]:
                current_idx -= 1
                continue
    
            output_page += self.build_article_item(article)
            current_idx -= 1
    
        output_page += """
    
    <div id="pagination">
    	<span class="hide">|</span> 
    	<a href="%s" class="button older">{older_entries}</a>
    </div>
    
    </section><!-- /#main -->
    
    """.format(**self.c('l10n')) % self.link("fullarchive.html")
    
        output_page += html_article_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.write("category/%s.html" % self.categories[indexed_category], output_page)
    
    def generate_archive_html(self, yearmonth):
        html_header = self.template("header.html")
        html_article_content_footer = self.template("article-content-footer.html")
        html_footer = self.template("footer.html")
    
        output_page = html_header
        output_page += """
    <div id="content" class="blog post multiple">
    
    <header role="page">
        <h1>%s</h1>
    	<p>{full_archive_content} %s.
        <a href="%s">{full_archive}</a></p>
    </header>
    	
    <section id="main">
    
    """.format(**self.c('l10n')) % (yearmonth.strftime("%B %Y"), yearmonth.strftime("%B"), self.link("fullarchive.html"))
    
        current_idx = self.get_highest_index()
    
        for i in range(self.get_highest_index()):
            article = self.parse_article(current_idx)
    
            if article["date"].year != yearmonth.year or article["date"].month != yearmonth.month:
                current_idx -= 1
                continue
    
            output_page += self.build_article_item(article)
            current_idx -= 1
    
        output_page += """
    
    <div id="pagination">
    	<span class="hide">|</span> 
    	<a href="%s" class="button older">{older_entries}</a>
    </div>
    
    </section><!-- /#main -->
    
    """.format(**self.c('l10n')) % self.link("fullarchive.html")
    
        output_page += html_article_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        date_filename = yearmonth.strftime("%b-%Y").lower()
        self.write("archive/%s.html" % date_filename, output_page)
    
    def generate_full_archive(self):
        html_header = self.template("header.html")
        html_article_content_footer = self.template("article-content-footer.html")
        html_footer = self.template("footer.html")
    
        output_page = html_header
        output_page += """
    <div id="content" class="blog post multiple">
    
    <header role="page">
        <h1>{news_archive}</h1>
    	<p>{news_archive_content}</p>
    </header>
    	
    <section id="main">
    
    <ul id="archive">
    """.format(**self.c('l10n'))
    
        current_idx = self.get_highest_index()
    
        for i in range(self.get_highest_index()):
            article = self.parse_article(current_idx)
            link = self.link(self.article_output_filename(article))
    
            output_page += """
        <li>
            <a href="%s">%s</a>
            <span class="meta">%s</span>
        </li>
    """ % (link, article["title"], article["date"].strftime("%A, %B, %Y"))
    
            current_idx -= 1
    
        output_page += """
    
    </ul>
    
    </section><!-- /#main -->
    
    """
    
        output_page += html_article_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.write("fullarchive.html", output_page)
    

    def generate_article(self, idx):
        article = self.parse_article(idx)
    
        html_header = self.template("header.html", {
            "title": article["title"]
        })
        html_article_content_footer = self.template("article-content-footer.html")
        html_footer = self.template("footer.html")
    
        output_page = html_header
        output_page += """
    <div id="content" class="blog post single">
    
    <header role="post">
    	<p class="meta"><time pubdate="">%s</time></p>
        <h1>%s</h1>
    </header>
    	
    <section id="main">
    
    <article>
    	<div class="group">
        """ % (
            article["date"].strftime("%A, %b %d, %Y"),
            article["title"])
    
        # Now add main text in
        buffer_line = ""
    
        for line in article["main"].split("\n"):
    
            if "\\\\" in line:
                line = line.split("\\\\")[0][:-1]
                buffer_line += line
                continue
    
            if buffer_line:
                line = buffer_line + " " + line
                buffer_line = ""
    
            # Add preview thumbnail picture
            if line == "@preview":
    	        output_page += """
        <div class="img-wrap post-image"><img src="%s" class="border" alt="image"></div>
        """ % article["preview"]
    
            elif line.startswith("@banner:"):
                assert len(line.split(":")) == 2
                params = line.split(":")[1].strip()
                output_page += banner_tag(params)
    
            elif line.startswith("@image:"):
                assert len(line.split(":")) == 2
                params = line.split(":")[1].strip()
                assert len(params.split(" ")) > 1
                remaining_params = " ".join(params.split(" ")[1:])
                link = params.split(" ")[0]
                output_page += """
        <a href="%s">%s</a>
                """ % (link, banner_tag(remaining_params))
    
            elif line.startswith("@smallpic:"):
                assert len(line.split(":")) == 2
                img_url = line.split(":")[1].strip()
                output_page += """
        <div class="img-wrap post-image"><img src="%s" class="border" alt="image"></div>
                """ % img_url
    
            elif line.startswith("https://www.youtube.com/"):
                video_id = line.split("?v=")[1]
                # Strip the &stuff
                video_id = video_id.split("&")[0]
                output_page += """
    <iframe src="https://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>
                """ % video_id
    
            elif line.startswith("@altvid:"):
                assert len(line.split(":")) == 2
                video_url = line.split(":")[1].strip()
                output_page += """
        <p><span class="caption"><a href="%s">Alternative download link</a></span></p>
                """ % video_url
    
            # Just a normal paragraph
            else:
                output_page += "%s\n" % line
    
        link, ident = self.disqus_data(article)
        output_page += """
        </div>
    
    <section id="comments">
    <div id="disqus_thread"></div>
    <script>
        /**
         *  RECOMMENDED CONFIGURATION VARIABLES: EDIT AND UNCOMMENT THE SECTION BELOW TO INSERT DYNAMIC VALUES FROM YOUR PLATFORM OR CMS.
         *  LEARN WHY DEFINING THESE VARIABLES IS IMPORTANT: https://disqus.com/admin/universalcode/#configuration-variables
         */
        /*
        var disqus_config = function () {
            this.page.url = '%s';  // Replace PAGE_URL with your page's canonical URL variable
            this.page.identifier = '%s'; // Replace PAGE_IDENTIFIER with your page's unique identifier variable
        };
        */
        (function() {  // DON'T EDIT BELOW THIS LINE
            var d = document, s = d.createElement('script');
            
            s.src = '//rojavaplan.disqus.com/embed.js';
            
            s.setAttribute('data-timestamp', +new Date());
            (d.head || d.body).appendChild(s);
        })();
    </script>
    <noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript" rel="nofollow">comments powered by Disqus.</a></noscript>
    </article>
    </section><!-- /#comments -->
    
    </section><!-- /#main -->
    
    """ % (link, ident)
    
        output_page += html_article_content_footer
        output_page += "</div><!-- /#content -->\n"
        output_page += html_footer
    
        self.mkdir_p(self.article_output_path(article))
        self.write(self.article_output_filename(article), output_page)

def main(lang='en'):
    import locale
    locale.setlocale(locale.LC_TIME, _cfg('locale',lang=lang))
    generator= Generator(lang)
    generator.generate()

main()
main('es')
