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
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-warning']) &gt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-warning': minimum cardinality of 'extension' is 1</sch:assert>
      <sch:assert test="count(f:extension[@url = 'http://hl7.org/fhir/StructureDefinition/valueset-warning']) &lt;= 1">extension with URL = 'http://hl7.org/fhir/StructureDefinition/valueset-warning': maximum cardinality of 'extension' is 1</sch:assert>
      <sch:assert test="count(f:expansion) &gt;= 1">expansion: minimum cardinality of 'expansion' is 1</sch:assert>
    </sch:rule>
  </sch:pattern>
  <sch:pattern>
    <sch:title>f:ValueSet/f:extension</sch:title>
    <sch:rule context="f:ValueSet/f:extension">
      <sch:assert test="count(f:id) &lt;= 1">id: maximum cardinality of 'id' is 1</sch:assert>
      <sch:assert test="count(f:url) &gt;= 1">url: minimum cardinality of 'url' is 1</sch:assert>
      <sch:assert test="count(f:url) &lt;= 1">url: maximum cardinality of 'url' is 1</sch:assert>
      <sch:assert test="count(f:value[x]) &gt;= 1">value[x]: minimum cardinality of 'value[x]' is 1</sch:assert>
      <sch:assert test="count(f:value[x]) &lt;= 1">value[x]: maximum cardinality of 'value[x]' is 1</sch:assert>
    </sch:rule>
  </sch:pattern>
  <sch:pattern>
    <sch:title>f:ValueSet/f:expansion/f:contains</sch:title>
    <sch:rule context="f:ValueSet/f:expansion/f:contains">
      <sch:assert test="count(f:code) &gt;= 1">code: minimum cardinality of 'code' is 1</sch:assert>
    </sch:rule>
  </sch:pattern>
</sch:schema>
