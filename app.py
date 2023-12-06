import ebooklib
from ebooklib import epub
import streamlit as st
import base64
from tempfile import NamedTemporaryFile
import os


st.set_page_config(initial_sidebar_state="collapsed")

def close_book():
    st.session_state['chapter_idx'] = 0
    st.session_state['page'] = "Home"
    st.session_state['book_file'] = None
    if os.path.exists("tmp.epub"):
        os.remove("tmp.epub")

def get_doc_idx_from_toc_idx(toc_idx):
    return book_docs.index(book.get_item_with_href(book_toc[toc_idx].href))

def get_chapter_content(chapter_idx):
    current_doc_idx = get_doc_idx_from_toc_idx(chapter_idx)
    next_doc_idx = get_doc_idx_from_toc_idx(chapter_idx+1) if chapter_idx+1 < len(book_toc) else None

    full_content = ""
    # for all docs before next chapter
    if next_doc_idx is not None:
        for idx in range(current_doc_idx, next_doc_idx):
            html_content = book_docs[idx].get_body_content().decode("utf-8")
            #iterate over all images in the html content
            for img_src in html_content.split('src="')[1:]:
                img_src = img_src.split('"')[0]
                img_data = book.get_item_with_href(img_src[3:]).get_content() # remove "../" from the image source
                img_uri = 'data:image/jpeg;base64,' + str(base64.b64encode(img_data).decode("utf-8"))
                # set image width to fit container
                html_content = html_content.replace(img_src, img_uri + '" width="100%"')
            full_content += html_content + "<br><br>"
    return full_content

def scroll_to_top():
    st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)

def set_current_chapter(toc_idx):
    scroll_to_top()
    st.session_state['chapter_idx'] = toc_idx

# Initialize session state
if 'page' not in st.session_state: st.session_state['page'] = "Home"
if 'book_file' not in st.session_state: st.session_state['book_file'] = None
if 'chapter_idx' not in st.session_state: st.session_state['chapter_idx'] = 0

if st.session_state['page'] == "Home":
    # Home page
    st.title("Epub Reader")
    book_file = st.file_uploader("Upload your book", type=["epub"])
    if book_file is not None:
        if os.path.exists("tmp.epub"):
            os.remove("tmp.epub")
        bytes_data = book_file.read()
        
        tmp = NamedTemporaryFile(delete=False, suffix='.epub')
        tmp.write(bytes_data) 
        book = epub.read_epub(tmp.name)
        epub.write_epub('tmp.epub', book)
        tmp.close()
        os.unlink(tmp.name)

        st.session_state['page'] = "Book"
        st.session_state['chapter_idx'] = 0
        st.rerun()

elif st.session_state['page'] == "Book":
    # Book page
    if os.path.exists("tmp.epub"):
        book = epub.read_epub('tmp.epub')
    else:
        st.session_state['page'] = "Home"
        st.session_state['book_file'] = None
        st.session_state['chapter_idx'] = 0
        st.rerun()

    book_toc = book.toc
    book_docs = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    st.title(book.title)

    # Sidebar
    close = st.sidebar.button("Close Book")
    if close:
        close_book()
        st.rerun()
    st.sidebar.title("Table of Content")
    for idx, item in enumerate(book_toc):
        st.sidebar.button(item.title, on_click=lambda idx=idx: set_current_chapter(idx))

    # Chapter content
    with st.spinner("waiting"):
        chapter_content = get_chapter_content(st.session_state['chapter_idx'])
    st.markdown(chapter_content, unsafe_allow_html=True)
