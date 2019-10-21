import toml
from Jumpscale import j


class SlideShow:
    def __init__(self):
        self.slides = []

    def slide_add(self, name, presentation_guid, footer, order):
        self.slides.append(Slide(name, presentation_guid, footer, order))

    def add_range(self, name, presentation_guid, range_start, range_end):
        for i in range(range_start, range_end + 1):
            self.slides.append(Slide(name, presentation_guid, order=i))

    def slides_get(self):
        # return sorted(self.slides, key=lambda slide: slide.order)
        return self.slides


class Slide:
    def __init__(self, name, presentation_guid, footer="", order=-1):
        self.name = name
        self.presentation_guid = presentation_guid
        self.footer = footer
        # TODO save the order as str and just cast it to string in start and end indexes of the range
        self.order = order


# toml_string = """
# [[presentation]]
# fruits = "www.google.com/presentaions/...."
# cars = "www.google.com/presentaions/...."
# books = "www.google.com/presentaions/...."

# [[slideshow]]
# presentation =  "fruits"
# slide = "4"

# [[slideshow]]
# presentation =  "fruits"
# slide = "5"

# [[slideshow]]
# presentation =  "cars"
# slide = "1,4:8,10,12:14"

# [[slideshow]]
# presentation =  "books"
# slide = "1,5,2,9"

# [[slideshow]]
# presentation =  "books"
# slide = "1:5"
# """


def is_valid_presentation_name(name, presentations):
    presentation = [item for item in presentations if name == item.get("name")]
    if presentation is not None:
        return presentation.pop()
    else:
        raise Exception("error in parsing the slideshow, There is no presentation given with this name")


def get_slide_numbers(slide_numbers):
    return slide_numbers.split(",")


def get_slide_range(range):
    ranges = range.split(":")
    return ranges[0], ranges[1]


def _content_parse(content):
    slideshow = SlideShow()
    # parsed_toml = toml.loads(content)
    parsed_toml = content
    print(parsed_toml)

    presentations = list()
    for key, val in parsed_toml["presentation"][0].items():
        presentation = dict()
        presentation["name"] = key
        presentation["value"] = val
        presentations.append(presentation)

    print(presentations)

    for slide in parsed_toml["slideshow"]:
        presentation = None
        presentation_name = slide.get("presentation")
        slide_numbers = slide.get("slide")
        if presentation_name is not None:
            presentation = is_valid_presentation_name(presentation_name, presentations)
        else:
            raise Exception("error in parsing the slideshow, There is an error in the presentation name")
        if slide_numbers is not None:
            slides_numbers_list = list()
            if slide_numbers.find(",") != -1:
                slides_numbers_list = get_slide_numbers(slide_numbers)
            else:
                slides_numbers_list.append(slide_numbers)

        else:
            raise Exception("error in parsing the slideshow, There is an error in the slide name")
        for number in slides_numbers_list:
            if number.find(":") != -1:
                range_start, range_end = get_slide_range(number)
                slideshow.add_range(
                    name="",
                    presentation_guid=presentation.get("value"),
                    range_start=int(range_start),
                    range_end=int(range_end),
                )
            else:
                slideshow.slide_add(name="", presentation_guid=presentation.get("value"), footer="", order=int(number))
    return slideshow


def slideshow_v2(doc, **kwargs):
    gdrive_cl = j.clients.gdrive.get("slideshow_macro_client", credfile="/sandbox/var/cred.json")
    slides_path = j.sal.fs.joinPaths("sandbox", "var", "gdrive", "static", "slide")
    j.sal.fs.createDir(slides_path)
    slides = _content_parse(kwargs)

    output = "```slideshow\n"
    for slide in slides.slides_get():
        # TODO remove this out side the for loop
        gdrive_cl.export_slides_with_ranges(slide.presentation_guid, slides_path)
        filepath = f"{slides_path}/{slide.presentation_guid}/{str(slide.order)}.png"
        dest = j.sal.fs.joinPaths(doc.docsite.outpath, doc.path_dir_rel, str(slide.order) + ".png")
        j.sal.bcdbfs.file_copy(filepath, dest)
        image_tag = """
        <img src="$path{dest}" alt='{slide_name}'"/>
        """.format(
            slide_name=slide.order, dest=dest
        )
        output += """
            <section>
               <div class="slide-image">
                   {image}
                   <div style="font-size: 200%;">
                   {footer}
                   </div>
               </div>
            </section>""".format(
            image=image_tag, footer=slide.footer
        )
    output += "\n```"
    return output
