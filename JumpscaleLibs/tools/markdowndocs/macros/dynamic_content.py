def render_dynamic_div(doc, actor, method, args):
    j = doc.docsite._j
    args_json = j.data.serializers.json.dumps(args)
    container_id = j.data.hash.md5_string(f"{actor}_{method}_{args_json}")

    return doc.render_macro_template(
        "dynamic_content.html", container_id=container_id, actor=actor, method=method, args=args_json
    )


def dynamic_content(doc, actor, method, **kwargs):
    html = render_dynamic_div(doc, actor, method, kwargs)
    return f"```inline_html\n{html}\n```"

