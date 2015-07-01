rule NonMatchingRule
{
	strings:
		$text_string = "nonexistent"

	condition:
		$text_string
}
