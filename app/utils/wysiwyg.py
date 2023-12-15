"""PC Est Magique - Wysiwyg utility"""

import json

def parse_delta_to_html(data: str) -> str:

    # TODO: list and header
    json_data = json.loads(data)['ops']
    final_html = ""
    for key in json_data:
        if 'attributes' in key.keys():
            if 'link' in key['attributes'].keys():
                l = key['attributes']['link']
                t = key['insert'].replace("\n", "<br/>")
                final_html += f'<a href="{l}" target="_blank">{t}</a>'
                continue
            tmp_begin = ""
            tmp_end = ""
            if 'bold' in key['attributes'].keys():
                tmp_begin += "<strong>"
                tmp_end += "</strong>"
            if 'italic' in key['attributes'].keys():
                tmp_begin += "<i>"
                tmp_end += "</i>"
            if 'underline' in key['attributes'].keys():
                tmp_begin += "<u>"
                tmp_end += "</u>"
            final_html += (tmp_begin
                        + key['insert'].replace("\n", "<br/>")
                        + tmp_end)
        else:
            final_html += key['insert'].replace("\n", "<br/>")
    return final_html
