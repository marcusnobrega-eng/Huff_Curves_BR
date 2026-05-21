from huff_curves_br.ana import _parse_ana_xml


def test_parse_ana_xml_normalizes_rainfall_depth_column():
    xml = """
    <DataTable>
      <Table>
        <CodEstacao>12345678</CodEstacao>
        <DataHora>01/02/2020 00:15:00</DataHora>
        <Chuva>1,5</Chuva>
        <Nivel>2,0</Nivel>
        <Vazao>3,5</Vazao>
      </Table>
    </DataTable>
    """

    df = _parse_ana_xml(xml)

    assert list(df.columns) == ["station_id", "datetime", "rainfall_mm", "stage_m", "flow_m3_s"]
    assert df.loc[0, "station_id"] == "12345678"
    assert df.loc[0, "rainfall_mm"] == 1.5
