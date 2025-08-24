from parser_sz import parse_sz
from parser_mb import parse_mb

if __name__ == '__main__':

    body = ''

    body_sz = parse_sz()
    if body_sz is not None:
        body += '<html><head></head><body>'
        body += '<div style="text-align: center">'
        body += '<a href="https://www.sparzinsen.at/">'
        body += '<img src="https://www.sparzinsen.at/wp-content/uploads/2023/02/SPARZINSEN.jpg" width="250" style="padding: 10px 0px 0px 0px"/>'
        body += '</a>'
        body += '</div>'
        body += body_sz

    body_mb = parse_mb()
    if body_mb is not None:
        if body:
            body += '<hr/>'
            body += '<div style="text-align: center">'
            body += '<a href="https://www.modern-banking.at">'
            body += '<img src="https://www.modern-banking.at/logo.png" width="250" style="padding: 30px 0px 0px 0px" />'
            body += '</a>'
            body += '</div>'
        else:
            body += '<html><head></head><body>'
            body += '<div style="text-align: center">'
            body += '<a href="https://www.modern-banking.at">'
            body += '<img src="https://www.modern-banking.at/logo.png" width="250" style="padding: 10px 0px 0px 0px" />'
            body += '</a>'
            body += '</div>'
        body += body_mb

    if body:
        body += '</body></html>'

        print(body)

        subject = '[FinanzNews] Neuigkeiten'
        pipe_path = "/var/run/mailifier"
        command = subject + ';' + body
        
        with open(pipe_path, 'w') as pipe:
            pipe.write(command)