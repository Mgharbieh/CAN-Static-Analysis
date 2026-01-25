import QtQuick 6.10
import QtQuick.Controls 6.10

Item {
    visible: true
    implicitHeight: issueTextArea.contentHeight + 10
    implicitWidth: issueTextArea.contentWidth + 50

    property var scrollRef: null

    Rectangle {
        id: issueTitleBar
        color: accent1color
        /*
        anchors {
            left: parent.left
            right: parent.right
            //leftMargin: 5
        }
        */
        x: scrollRef ? scrollRef.contentItem.contentX : 0
        width: scrollRef ? scrollRef.availableWidth : parent.width
        height: 40
        radius: 10

        Text {
            id: issueTitleText
            anchors {
                top: parent.top
                left: parent.left
                bottom: parent.bottom
                topMargin: -2
                leftMargin: 5
            }
            text: ""
            color: "#FFFFFF" //change to titleTextColor variable later
            font.pixelSize: 30
            font.bold: true
            //verticalAlignment: Text.AlignVCenter
        }
    }

    TextArea {
        id: issueTextArea
        anchors {
            top: issueTitleBar.bottom
            left: parent.left
            leftMargin: 10
        }

        text: ""
        color: textColor
        font.pixelSize: 25
        readOnly: true
        wrapMode: TextEdit.NoWrap
        background: Rectangle {
            color: backgroundcolor2
            radius: 15
        }
    }

    function populateModule(titleString, issueString) {
        issueTitleText.text = titleString
        issueTextArea.text = issueString
    }
}