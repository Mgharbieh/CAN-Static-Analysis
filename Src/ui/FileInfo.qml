import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Effects 6.10
import QtQuick.Layouts 6.10

ApplicationWindow {
    id: windowRoot

    width: screen.width * 0.8  //100//500
    height: screen. height * 0.8 //100//500
    visible: false

    title: ""
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint

    Rectangle {
        id: windowFiller
        radius: 15
        anchors.fill: parent
        color: backgroundcolor
        border.color: backgroundcolor2
        border.width: 1
        clip: true

        InfoTitleBar {
            id: infoTitleBar
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                margins: 1
            }
        }

        RectangularShadow {
            anchors.fill: sourceCodeRect
            offset.x: 5 
            offset.y: 5 
            radius: sourceCodeRect.radius
            blur: 20 // Shadow softness
            spread: 0 // Shadow size relative to source
            color: "#80000000" // Shadow color with alpha (black, 50% opacity)
            antialiasing: true // Smooth the edges
        }

        Rectangle {
            id: sourceCodeRect
            anchors {
                top: infoTitleBar.bottom
                left: parent.left
                margins: 15
            }

            width: 0.55 * parent.width
            height: 0.55 * parent.height
            radius: 15
            color: backgroundcolor2

            ScrollView {
                id: viewSourceCode
                anchors.fill: parent
                anchors.margins: 6
                clip: true 

                
                ScrollBar.vertical: ScrollBar {
                    parent: viewSourceCode
                    x: viewSourceCode.mirrored ? 0 : viewSourceCode.width - width
                    y: viewSourceCode.topPadding
                    height: viewSourceCode.availableHeight
                    policy: ScrollBar.AsNeeded
                    interactive: true
                    padding: 0

                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: width / 2
                        color: '#2e2e2e'
                    }
                    background: Rectangle {
                        implicitWidth: 10
                        //radius: width / 2
                        color: backgroundcolor2
                    }
                }
                
                ScrollBar.horizontal: ScrollBar {
                    parent: viewSourceCode
                    x: viewSourceCode.leftPadding
                    y: viewSourceCode.height - height
                    width: viewSourceCode.availableWidth
                    policy: ScrollBar.AsNeeded
                    padding: 0

                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: width / 2
                        color: '#2e2e2e'
                    }
                    background: Rectangle {
                        implicitWidth: 10
                        //radius: width / 2
                        color: backgroundcolor2
                    }
                }

                background: Rectangle {
                    color: backgroundcolor2
                    radius: sourceCodeRect.radius
                }
                
                TextArea {
                    id: sourceCodeText
                    text: ""
                    color: "#FFFFFF"
                    font.pixelSize: 20
                    readOnly: true
                    wrapMode: TextEdit.NoWrap
                    width: parent.width // Bind width to the ScrollView's available width
                    height: parent.height
                    background: Rectangle {
                        color: backgroundcolor2
                        radius: 15
                    }
                }
            }
        }

        RectangularShadow {
            anchors.fill: issuesRect
            offset.x: 5 
            offset.y: 5 
            radius: sourceCodeRect.radius
            blur: 20 // Shadow softness
            spread: 0 // Shadow size relative to source
            color: "#80000000" // Shadow color with alpha (black, 50% opacity)
            antialiasing: true // Smooth the edges
        }

        Rectangle {
            id: issuesRect
            anchors {
                top: infoTitleBar.bottom
                left: sourceCodeRect.right
                right: parent.right
                margins: 15
            }

            height: 0.55 * parent.height
            radius: 10
            color: backgroundcolor2

            ScrollView {
                id: viewIssues
                anchors.fill: parent
                anchors.margins: 6
                clip: true 

                ScrollBar.vertical: ScrollBar {
                    parent: viewIssues
                    x: viewIssues.mirrored ? 0 : viewIssues.width - width
                    y: viewIssues.topPadding
                    height: viewIssues.availableHeight
                    policy: ScrollBar.AsNeeded
                    interactive: true
                    padding: 0

                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: width / 2
                        color: '#2e2e2e'
                    }
                    background: Rectangle {
                        implicitWidth: 10
                        color: backgroundcolor2
                    }
                }

                ScrollBar.horizontal: ScrollBar {
                    id: hBar
                    parent: viewIssues
                    x: viewIssues.leftPadding
                    y: viewIssues.height - height
                    width: viewIssues.availableWidth
                    policy: ScrollBar.AsNeeded
                    hoverEnabled: false
                    active: hovered || pressed

                    contentItem: Rectangle {
                        implicitHeight: 6
                        radius: height / 2
                        color: '#2e2e2e'
                    } 
                    background: Rectangle {
                        implicitHeight: 10
                        //radius: width / 2
                        color: backgroundcolor2
                        opacity: 1
                    }
                }

                background: Rectangle {
                    color: backgroundcolor2
                    radius: issuesRect.radius
                }

                ColumnLayout {
                    id: contentColumn
                    width: Math.max(viewIssues.availableWidth, implicitWidth)
                    spacing: 8 
                
                    IssuePane {
                        id: maskFiltPane
                        Layout.fillWidth: true
                        scrollRef: viewIssues
                    }

                    IssuePane {
                        id: rtrPane
                        Layout.fillWidth: true
                        scrollRef: viewIssues
                    }

                    IssuePane {
                        id: idLenPane
                        Layout.fillWidth: true
                        scrollRef: viewIssues
                    }

                    IssuePane {
                        id: dlcPane
                        Layout.fillWidth: true
                        scrollRef: viewIssues
                    }

                    IssuePane {
                        id: bytePackingPane
                        Layout.fillWidth: true
                        scrollRef: viewIssues
                    }
                }
                /*
                Column {
                    spacing: 2

                    IssuePane {id: maskFiltPane}
                    IssuePane {id: rtrPane}
                    IssuePane {id: idLenPane}
                    IssuePane {id: dlcPane}
                    IssuePane {id: bytePackingPane}
                }

                TextArea {
                    id: issueText
                    text: ""
                    color: "#FFFFFF"
                    font.pixelSize: 24
                    readOnly: true
                    wrapMode: TextEdit.NoWrap
                    width: parent.width // Bind width to the ScrollView's available width
                    background: Rectangle {
                        color: backgroundcolor2
                        radius: 15
                    }
                }
                */
            }
        }
    }

    function setFileInfo(code, infoStream) {
        console.log("setFileInfo called...")
        var temp = ""

        windowRoot.title = infoStream.file_name
        infoTitleBar.setTitleText(infoStream.file_name)
        sourceCodeText.text = code
        
        infoStream.mask_filt.mf_messages.forEach(function(item) {
            temp += ("• " + item) + "\n"
        })   
        maskFiltPane.populateModule("Mask and Filter (" + infoStream.mask_filt.mf_issues + ")", temp)

        temp = ""
        infoStream.rtr.rtr_messages.forEach(function(item) {
            temp += ("• " + item) + "\n"
        })
        rtrPane.populateModule("Remote Transmission Request (" + infoStream.rtr.rtr_issues + ")", temp)

        temp = ""
        infoStream.idLen.idLen_messages.forEach(function(item) {
            temp += ("• " + item) + "\n"
        })
        idLenPane.populateModule("ID Length (" + infoStream.idLen.idLen_issues + ")", temp)

        temp = ""
        infoStream.dlc.dlc_messages.forEach(function(item) {
            temp += ("• " + item) + "\n"
        })
        dlcPane.populateModule("Data Length Code (" + infoStream.dlc.dlc_issues + ")", temp)

        temp = "pls fix serene"
        // datalength code here when fixed //
        bytePackingPane.populateModule("Byte Packing Violations", temp)

        /*
        issueText.text = "Mask and Filter (" + infoStream.mask_filt.mf_issues + ")\n"
        infoStream.mask_filt.mf_messages.forEach(function(item) {
            issueText.text += ("  " + item) + "\n"
        })
        issueText.text += "\nRemote Transmission Request (" + infoStream.rtr.rtr_issues + ")\n"
        infoStream.rtr.rtr_messages.forEach(function(item) {
            issueText.text += ("  " + item) + "\n"
        })
        issueText.text += "\nID Length (" + infoStream.idLen.idLen_issues + ")\n"
        infoStream.idLen.idLen_messages.forEach(function(item) {
            issueText.text += ("  " + item) + "\n"
        })
        issueText.text += "\nData Length Code (" + infoStream.dlc.dlc_issues + ")\n"
        infoStream.dlc.dlc_messages.forEach(function(item) {
            issueText.text += ("  " + item) + "\n"
        })
        */
        windowRoot.visible = true
    }
}