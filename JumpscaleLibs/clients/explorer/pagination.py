def get_page(session, page, model, url, query=None):
    if not query:
        query = {}
    query["page"] = page
    resp = session.get(url, params=query)
    output = []
    for data in resp.json():
        obj = model.new(datadict=data)
        output.append(obj)
    pages = int(resp.headers.get("Pages", 0))
    return output, pages


def get_all(session, model, url, query=None):
    iter, pages = get_page(session, 1, model, url, query)
    yield from iter
    for i in range(2, pages):
        obj, _ = get_page(i)
        yield from iter
