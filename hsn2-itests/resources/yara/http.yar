rule response_200
{

    strings:
        $text_string = "HTTP/1.1 200 OK"

    condition:
        $text_string

}

rule GET
{

    strings:
        $text_string = /GET \/.* HTTP\/1.1/

    condition:
        $text_string

}

rule POST
{

    strings:
        $text_string = /POST \/.* HTTP\/1.1/

    condition:
        $text_string

}

rule PUT
{

    strings:
        $text_string = /POST \/.* HTTP\/1.1/

    condition:
        $text_string

}
