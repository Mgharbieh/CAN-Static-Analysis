import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Effects 6.10

Rectangle {
    id: titleBar
    height: 30
    width: parent.width
    color: backgroundcolor // Custom color
    radius: 10

    Rectangle {
        id: closeButtonRect
        anchors {
            right: parent.right
            bottom: parent.bottom
            top: parent.top
        }

        width: 30
        color: backgroundcolor

        Text {
            id: closeButtonText
            text: "✕"
            font.pixelSize: 20
            anchors.centerIn: parent
            color: "#FFFFFF"
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
        
            onEntered: closeButtonRect.color = "#FF0000"
            onExited: closeButtonRect.color = backgroundcolor 
            onClicked: root.close()
        }
    
    }

    Rectangle {
        id: minimizeButtonRect
        anchors {
            right: closeButtonRect.left
            bottom: parent.bottom
            top: parent.top
        }

        width: 30
        color: backgroundcolor

        Text {
            id: minimizeButtonText
            text: "—"
            font.pixelSize: 15
            anchors.centerIn: parent
            color: "#FFFFFF"
        }

        MouseArea {
            id: mouseArea2
            anchors.fill: parent
            hoverEnabled: true

            onEntered: minimizeButtonRect.color = backgroundcolor2
            onExited: minimizeButtonRect.color = backgroundcolor
            onClicked: root.showMinimized()
        }
}


    DragHandler {
        onActiveChanged: if (active) root.startSystemMove()
        target: null // The entire Rectangle acts as the drag area
    }   

}