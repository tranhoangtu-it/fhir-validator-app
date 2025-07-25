<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
  <sch:ns prefix="f" uri="http://hl7.org/fhir"/>
  <sch:ns prefix="h" uri="http://www.w3.org/1999/xhtml"/>
  <!-- 
    This file contains just the constraints for the profile ShareableValueSet
    It includes the base constraints for the resource as well.
    Because of the way that schematrons and containment work, 
    you may need to use this schematron fragment to build a, 
    single schematron that validates contained resources (if you have any) 
  -->
  <sch:pattern>
    <sch:title>f:ValueSet</sch:title>
    <sch:rule context="f:ValueSet">
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-authoritativeSource']) &lt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-authoritativeSource': maximum cardinality of 'extension' is 1</sch:assert>
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-rules-text']) &lt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-rules-text': maximum cardinality of 'extension' is 1</sch:assert>
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-expression']) &lt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-expression': maximum cardinality of 'extension' is 1</sch:assert>
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-supplement']) &lt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-supplement': maximum cardinality of 'extension' is 1</sch:assert>
    </sch:rule>
  </sch:pattern>
</sch:schema>
