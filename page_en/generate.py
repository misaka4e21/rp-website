# -*- coding: utf-8 -*-
import os
import sys
import datetime
import hashlib

def get_highest_index():
    highest_idx = 0
    for filename in os.listdir("articles/"):
        try:
            idx = int(filename)
        except ValueError:
            pass
        else:
            if idx > highest_idx:
                highest_idx = idx
    return highest_idx

def article_filename(idx):
    filename = str(idx)
    filename = "0" * (4 - len(filename)) + filename
    return filename

def translate_category(category):
    mappings = {
        # None
    }
    if category not in mappings.keys():
        return category
    return mappings[category]

def disqus_data(article):
    link = "http://RojavaPlan.com" + \
        interface.link(article_output_filename(article))
    ident = hashlib.md5(link).hexdigest()
    return link, ident

def parse_article(interface, idx):
    try:
        raw = interface.raw_article(idx)
    except IOError:
        return None
    sections = raw.split("---\n")
    assert(len(sections) == 3)
    title_data = tuple(sections[0].split("\n")[:-1])
    assert(len(title_data) == 5)
    date = datetime.datetime.strptime(title_data[1], "%b %d, %Y")
    categories = [category.strip() for category in title_data[3].split(",")]
    # Translate them to foreign language if needed
    categories = [translate_category(category) for category in categories]
    return {
        "title": title_data[0],
        "date": date,
        "preview": title_data[2],
        "comments_url": title_data[4],
        "categories": categories,
        "blurb": sections[1],
        "main": sections[2]
    }

def generate_index_html(interface):
    html_header = interface.template("header.html")
    html_footer = interface.template("footer.html")

    html_index_content_header = interface.template("index-content-header.html")
    output_page = html_header + html_index_content_header
    current_idx = get_highest_index()

    for i in range(4):
        article = parse_article(interface, current_idx)
        if not article:
            break
        link = interface.link(article_output_filename(article))
        date_formatted = article["date"].strftime("%b %d, %Y")
        output_page += """
        <article>
            <a href="%s"><img src="%s" class="border" alt="image">
            <h1>%s</h1></a>
            <p>%s</p>
            <p class="meta"><time pubdate="">%s</time> / <a href="%s">Read »</a></p>
        </article>
        """ % (link, article["preview"], article["title"], article["blurb"],
               date_formatted, link)
        current_idx -= 1

    output_page += """

<div id="pagination">
	<span class="hide">|</span> 
	<a href="%s" class="button older">Older Entries »</a>
</div>

</section><!-- /#main -->

</div><!-- /#content -->

""" % interface.link("fullarchive.html")

    output_page += html_footer

    interface.write("index.html", output_page)

def build_gallery(interface, name):
    html_header = interface.template("header.html")
    html_footer = interface.template("footer.html")

    html_page_content = interface.template("%s-content.html" % name)
    output_page = html_header
    output_page += '<div id="content" class="gallery">\n'
    output_page += html_page_content
    output_page += "</div><!-- /#content -->\n"
    output_page += html_footer

    interface.write("%s.html" % name, output_page)

def build_main_page(interface, name):
    html_header = interface.template("header.html")
    html_footer = interface.template("footer.html")

    html_page_content = interface.template("%s-content.html" % name)
    html_mainpages_content_footer = interface.template("mainpages-content-footer.html")
    output_page = html_header
    output_page += '<div id="content" class="page">\n'
    output_page += html_page_content
    output_page += html_mainpages_content_footer
    output_page += "</div><!-- /#content -->\n"
    output_page += html_footer

    interface.write("%s.html" % name, output_page)

def article_output_path(article):
    return "articles/%s/%s/" % (
        article["date"].year, article["date"].month)

def article_output_filename(article):
    filename = article["title"].replace(" ", "-")
    filename = filename.replace("?", "").replace("!", "").replace(".", "")
    filename = filename.lower()
    return "%s%s.html" % (article_output_path(article), filename)

def build_article_item(interface, article, categories):
    link = interface.link(article_output_filename(article))
    disqus_link, ident = disqus_data(article)
    item = """
<article>

	<header>
		<h1><a href="%s">%s</a></h1>
	</header>
		
	<div class="group">
		<div class="img-wrap post-image"><img src="%s" class="border" alt="image"></div>
        <p>%s</p>
		<p><a href="%s">Continue reading »</a></p>
    </div>

	<footer>
		<ul>
			<li class="date"><time datetime="2012-05-17T08:35-05:00" pubdate=""><span>%s</span> <em>%s</em></time></li>
			<li class="comments"><a href="%s#disqus_thread" data-disqus-identifier="%s">Leave a comment</a></li>
			<li class="tags">
""" % (link, article["title"], article["preview"], article["blurb"], link,
       article["date"].year, article["date"].strftime("%b %d"),
       link, ident)

    for category in article["categories"]:
        try:
            category_handle = categories[category]
        except KeyError:
            print >> sys.stderr, "************************************************"
            print >> sys.stderr, "Error: Non existant category: %s" % category
            print >> sys.stderr, "************************************************"
            raise Exception("Non existant category: %s" % category)
        category_link = interface.link("category/%s.html" % category_handle)
        item += '<a href="%s">%s</a> ' % (category_link, category)

    item += """
            </li>
		</ul>
	</footer>
		
</article>
"""
    return item

def generate_news_html(interface, categories):
    html_header = interface.template("header.html")
    html_article_content_footer = interface.template("article-content-footer.html")
    html_footer = interface.template("footer.html")

    output_page = html_header
    output_page += """
<div id="content" class="blog post multiple">

<header role="page">
    <h1 class="blog icon">News</h1>
	<p>Follow the latest goings ons in the revolutionary world of Rojava.</p>
</header>
	
<section id="main">

"""

    current_idx = get_highest_index()

    for i in range(4):
        article = parse_article(interface, current_idx)
        if not article:
            break
        output_page += build_article_item(interface, article, categories)
        current_idx -= 1

    output_page += """

<div id="pagination">
	<span class="hide">|</span> 
	<a href="%s" class="button older">Older Entries »</a>
</div>

</section><!-- /#main -->

""" % interface.link("fullarchive.html")

    output_page += html_article_content_footer
    output_page += "</div><!-- /#content -->\n"
    output_page += html_footer

    interface.write("news.html", output_page)

def generate_category_html(interface, indexed_category, limit, categories):
    html_header = interface.template("header.html")
    html_article_content_footer = interface.template("article-content-footer.html")
    html_footer = interface.template("footer.html")

    output_page = html_header
    output_page += """
<div id="content" class="blog post multiple">

<header role="page">
    <h1>%s</h1>
	<p>Displaying all news items tagged with "%s".</p>
</header>
	
<section id="main">

""" % (indexed_category, indexed_category)

    current_idx = get_highest_index()

    for i in range(get_highest_index()):
        article = parse_article(interface, current_idx)

        if indexed_category not in article["categories"]:
            current_idx -= 1
            continue

        output_page += build_article_item(interface, article, categories)
        current_idx -= 1

    output_page += """

<div id="pagination">
	<span class="hide">|</span> 
	<a href="%s" class="button older">Older Entries »</a>
</div>

</section><!-- /#main -->

""" % interface.link("fullarchive.html")

    output_page += html_article_content_footer
    output_page += "</div><!-- /#content -->\n"
    output_page += html_footer

    interface.write("category/%s.html" % categories[indexed_category], output_page)

def generate_archive_html(interface, yearmonth, categories):
    html_header = interface.template("header.html")
    html_article_content_footer = interface.template("article-content-footer.html")
    html_footer = interface.template("footer.html")

    output_page = html_header
    output_page += """
<div id="content" class="blog post multiple">

<header role="page">
    <h1>%s</h1>
	<p>Displaying all news entries for the month of %s.
    <a href="%s">Full archive »</a></p>
</header>
	
<section id="main">

""" % (yearmonth.strftime("%B %Y"), yearmonth.strftime("%B"), interface.link("fullarchive.html"))

    current_idx = get_highest_index()

    for i in range(get_highest_index()):
        article = parse_article(interface, current_idx)

        if article["date"].year != yearmonth.year or article["date"].month != yearmonth.month:
            current_idx -= 1
            continue

        output_page += build_article_item(interface, article, categories)
        current_idx -= 1

    output_page += """

<div id="pagination">
	<span class="hide">|</span> 
	<a href="%s" class="button older">Older Entries »</a>
</div>

</section><!-- /#main -->

""" % interface.link("fullarchive.html")

    output_page += html_article_content_footer
    output_page += "</div><!-- /#content -->\n"
    output_page += html_footer

    date_filename = yearmonth.strftime("%b-%Y").lower()
    interface.write("archive/%s.html" % date_filename, output_page)

def generate_full_archive(interface):
    html_header = interface.template("header.html")
    html_article_content_footer = interface.template("article-content-footer.html")
    html_footer = interface.template("footer.html")

    output_page = html_header
    output_page += """
<div id="content" class="blog post multiple">

<header role="page">
    <h1>News Archive</h1>
	<p>Every news article we've published lies here.</p>
</header>
	
<section id="main">

<ul id="archive">
"""

    current_idx = get_highest_index()

    for i in range(get_highest_index()):
        article = parse_article(interface, current_idx)
        link = interface.link(article_output_filename(article))

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

    interface.write("fullarchive.html", output_page)

def banner_tag(params):
    img_url = params.split(" ")[0]
    caption = " ".join(params.split(" ")[1:])
    # Add <span> tags if there's a provided caption.
    span_caption = '<span class="caption">%s</span>' % caption if caption else ""
    return """
<div class="img-wrap post-banner"><img src="%s" class="border" alt="%s">%s</div>
    """ % (img_url, caption, span_caption)

def generate_article(interface, idx):
    article = parse_article(interface, idx)

    html_header = interface.template("header.html", {
        "title": article["title"]
    })
    html_article_content_footer = interface.template("article-content-footer.html")
    html_footer = interface.template("footer.html")

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

    link, ident = disqus_data(article)
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

    interface.mkdir_p(article_output_path(article))
    interface.write(article_output_filename(article), output_page)

class Interface:

    def __init__(self):
        self.build_prefix = "/var/www/html/"
        self.data_prefix = "/"
        self.link_prefix = "/"
        self.articles_prefix = "articles/"
        # Must end in a /
        assert self.link_prefix[-1] == "/", "Must end in a /"
        self.params = {
            "title": "What you've been waiting for.",
            "data_prefix": self.data_prefix,
            "prefix": self.link_prefix
        }

    def _filter(self, page, user_params):
        params = self.params.copy()
        params.update(user_params)
        for name, value in params.iteritems():
            var_name = "${%s}" % name
            page = page.replace(var_name, value)
        return page

    def link(self, url):
        return self.link_prefix + url

    def template(self, name, user_params={}):
        return self._filter(open("templates/%s" % name).read(), user_params)

    def write(self, pagename, page):
        open(self.build_prefix + pagename, "w").write(page)

    def raw_article(self, idx, user_params={}):
        filename = self.articles_prefix + article_filename(idx)
        return self._filter(open(filename).read(), user_params)

    def mkdir_p(self, path):
        path = self.build_prefix + path
        if not os.path.exists(path):
            os.makedirs(path)

categories = {
    "Society":         "society",
    "Economy":         "economy",
    "Health":          "health",
    "Science & Tech":  "scitech",
    "Arts & Music":    "artsmusic",
    "Frontline":       "frontline",
    "World":           "world",
    "Video Reports":   "videoreports",
    "In Pictures":     "inpictures",
    "Special Reports": "specialreports",
    "Explainers":      "explainers",
    "Opinion":         "opinion"
}

interface = Interface()
interface.mkdir_p("category/")
interface.mkdir_p("archive/")
generate_index_html(interface)
build_gallery(interface, "rojavaplan")
build_main_page(interface, "join")
build_main_page(interface, "join-1-what-can-you-do")
build_main_page(interface, "join-2-learn-kurdish")
build_main_page(interface, "join-3-preparing-yourself")
build_main_page(interface, "join-3-1-resources")
build_main_page(interface, "join-3-2-personal-account")
build_main_page(interface, "join-4-the-journey")
build_main_page(interface, "join-5-what-to-expect")
build_main_page(interface, "join-6-ready")
build_main_page(interface, "contribute")
build_main_page(interface, "donate")
build_main_page(interface, "about")
build_main_page(interface, "faqs")
build_main_page(interface, "contact")
generate_news_html(interface, categories)
generate_full_archive(interface)

for category_name in categories.keys():
    generate_category_html(interface, category_name, 8, categories)

generate_archive_html(interface, datetime.date(2015, 11, 1), categories)

for i in range(get_highest_index()):
    generate_article(interface, i + 1)

