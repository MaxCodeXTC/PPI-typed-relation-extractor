<?xml version="1.0"  ?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:df="http://psi.hupo.org/mi/mif">

    <xsl:template match="/">
        <xsl:for-each select="/df:entrySet/df:entry/df:interactionList/df:interaction">
            <data>
                <xsl:copy-of select="."/>
                <xsl:variable name="entry" select="../.."/>
                <xsl:variable name="expid" select="df:experimentList/df:experimentRef/text()"/>

                <!-- experiments-->
                <xsl:copy-of select="$entry/df:experimentList/df:experimentDescription[@id = $expid]"/>

                <!-- Particiapants-->
                <xsl:for-each select="df:participantList/df:participant">
                    <xsl:variable name="partid" select="df:interactorRef/text()"></xsl:variable>
                    <xsl:copy-of select="$entry/df:interactorList/df:interactor[@id = $partid]"/>
                </xsl:for-each>
            </data>

        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>