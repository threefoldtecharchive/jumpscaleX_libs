def write_script(doc, unique_id, actor, method, args):
    """write javascript code that fetches the data and render it to certian div

    :param doc: curent doc
    :type doc: Doc
    :param unique_id: unique id for the script file and div
    :type unique_id: str
    :param actor: actor name
    :type actor: str
    :param method: method name
    :type method: str
    :param args: json-encoded arguments
    :type args: str
    :return: script src path (to include in html from /web/bcdbfs/...)
    :rtype: str
    """
    j = doc.docsite._j

    content = doc.render_macro_template(
        "dynamic_content_script.js", container_id=unique_id, actor=actor, method=method, args=args
    )

    script_name = f"script_{unique_id}.js"
    real_path = j.sal.fs.joinPaths(doc.docsite.outpath, doc.path_dir_rel, script_name)
    if j.sal.bcdbfs.exists(real_path):
        j.sal.bcdbfs.file_delete(real_path)
    j.sal.bcdbfs.file_write(real_path, content)

    rel_outpath = doc.docsite.outpath.lstrip("/")
    return j.sal.fs.joinPaths("/web/bcdbfs", rel_outpath, doc.path_dir_rel, script_name)


def dynamic_content(doc, actor, method, **kwargs):
    j = doc.docsite._j

    args_json = j.data.serializers.json.dumps(kwargs)
    unique_id = j.data.hash.md5_string(f"{actor}_{method}_{args_json}")

    script_path = write_script(doc, unique_id, actor, method, args_json)
    html = doc.render_macro_template("dynamic_content.html", container_id=unique_id, script_path=script_path)
    return f"```inline_html\n{html}\n```"
