<?xml version="1.0" encoding="ISO-8859-1" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <html>
            <body>
                <xsl:apply-templates select="stats/account">
                    <xsl:sort select="title"/>
                </xsl:apply-templates>
                <xsl:apply-templates select="stats/character">
                    <xsl:sort select="cid"/>
                </xsl:apply-templates>
            </body>
        </html>
    </xsl:template>
    <xsl:template match="account">
        <h1>
            Account: [<xsl:value-of select="aid"/>]
        </h1>
    </xsl:template>
    <xsl:template match="character">
        <h2>
            Character: [<xsl:value-of select="cid"/>]
        </h2>
        <h3>
            World: <xsl:value-of select="world"/>
        </h3>
        <xsl:apply-templates select="activity">
            <xsl:sort select="@date"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="activity">
        <h4>
            Activity - <xsl:value-of select="@date"/>
        </h4>
        <p style="overflow-wrap: break-word; font-family: monospace">
            <xsl:value-of select="."/>
        </p>
    </xsl:template>
</xsl:stylesheet>