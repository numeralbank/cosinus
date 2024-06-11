SELECT
	FormTable.cldf_parameterReference AS ID,
	LanguageTable.cldf_name AS DOCULECT,
	ParameterTable.Concepticon_Gloss AS CONCEPT,
	FormTable.cldf_form AS FORM,
	--LENGTH(FormTable.cldf_form) AS STRLENGTH,
	NULL AS TOKENS,
	NULL AS MORPHEMES,
	NULL AS COGIDS,
	NULL AS NOTE
FROM FormTable
LEFT JOIN LanguageTable
	ON FormTable.cldf_languageReference = LanguageTable.cldf_id
LEFT JOIN ParameterTable
	ON ParameterTable.cldf_id = FormTable.cldf_parameterReference
WHERE (
	CAST(FormTable.cldf_parameterReference AS int) BETWEEN 1 AND 40
	AND LanguageTable.Glottolog_Name IN ('Paraguayan Guaraní')
)
ORDER BY LanguageTable.cldf_name;
