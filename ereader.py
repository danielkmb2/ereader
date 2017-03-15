import os
import curses
import sys
from bs4 import BeautifulSoup
import html2text
import ebooklib
from ebooklib import epub
import cursesmenu
import pickle


class Book():

    def __init__(self, path):
        self.originalPath = path
        self.book = epub.read_epub(path)

    def getBookParsedSections(self):
        sections = []

        for section in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # get id, assume its the title (?)
            section_id = section.get_id()

            # parse encoded html into formatted text
            html_content = section.get_content()
            soup = BeautifulSoup(html_content, 'lxml')
            decoded_html = soup.decode_contents()
            section_text = html2text.html2text(decoded_html)

            # append this section to the whole list as a tuple (id, text)
            sections.append((section_id, section_text))

        return sections


class Reader:
    def __init__(self, screen, prefs, title, lines):
        self.prefs = prefs
        self.screen = screen
        self.title = title
        self.lines = lines
        self.rows = len(lines)
        self.cols = max(len(l) for l in lines)
        self.top = self.prefs.getCompletion(self.title)
        self.left = 0

        # logcal window for line texts
        self.pad = curses.newpad(self.rows + 1, self.cols)
        self.pad.keypad(1)  # accept arrow keys
        for i in range(len(lines)):
            self.pad.addstr(i, 0, lines[i])
            pass

    def show(self):
        size = self.screen.getmaxyx()  # current screen size
        self.pad.refresh(self.top, self.left, 0, 0, size[0] - 1, size[1] - 2)
        pass

    def do_command(self):
        ch = self.pad.getch()
        if ch == ord("q"):
            # we are quitting, save progress before
            if self.top > 0 and self.top <= len(self.lines):
                self.prefs.setCompletion(self.title, self.top)

            # also clear screen
            self.screen.clear()
            return False
        if ch == curses.KEY_UP:
            self.top = max(self.top - 1, 0)
            self.show()
            pass
        if ch == curses.KEY_DOWN:
            size = self.screen.getmaxyx()
            self.top = min(self.top + 1, self.rows - size[0])
            self.show()
            pass
        if ch == curses.KEY_LEFT:
            self.left = max(self.left - 1, 0)
            self.show()
            pass
        if ch == curses.KEY_RIGHT:
            size = self.screen.getmaxyx()
            self.left = min(self.left + 1, self.cols - size[1] + 1)
            self.show()
            pass
        return True
    pass


class Prefs:

    prefs = {}

    def __init__(self):
        # load preferences to a dictionary
        self.load()

    def getCompletion(self, sectionId):
        completion = self.prefs.get(sectionId)
        if completion is not None:
            return completion
        else:
            return 0

    def setCompletion(self, sectionId, completion):
        self.prefs[sectionId] = completion
        self.save()

    def save(self):
        pickle.dump(self.prefs, open("prefs.p", "wb"))

    def load(self):
        try:
            self.prefs = pickle.load(open("prefs.p", "rb"))
        except Exception:
            # no prefious preferences
            pass


def initiateReader(menu, prefs, title, lines):
    try:
        screen = curses.initscr()
        curses.noecho()     # no echo key input
        curses.cbreak()     # input with no-enter keyed
        curses.curs_set(0)  # hide cursor
        page = Reader(screen, prefs, title, lines)
        page.show()
        while page.do_command():
            pass

    finally:
        curses.curs_set(1)
        curses.echo()
        curses.endwin()
        menu.show()
        pass
    pass


def showBookSections(bookPath, prefs):
    book = Book(bookPath)
    bookSections = book.getBookParsedSections()
    menu = cursesmenu.CursesMenu("Epub reader", "Chapter selection")

    functionItem = cursesmenu.items.FunctionItem
    for title, text in bookSections:
        lines = text.split("\n")
        completion = prefs.getCompletion(title)
        menuTitle = title + ": " + str(completion) + "/" + str(len(lines))
        menuEntry = functionItem(menuTitle, initiateReader,
                                 [menu, prefs, title, lines])
        menu.append_item(menuEntry)

    menu.show()


prefs = Prefs()
path = sys.argv[1]
if os.path.isfile(path) and path.endswith(".epub"):
    showBookSections(path, prefs)
else:
    # print error
    pass
