rule TextExample
{
	strings:
		$text_string = "foobar"

	condition:
		$text_string
}

rule AnotherTextExample
{
	strings:
		$text_string = "foo"

	condition:
		$text_string
}
