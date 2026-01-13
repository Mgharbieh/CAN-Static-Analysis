import QtQuick 6.10
import QtQuick.Controls 6.10
import QtQuick.Effects 6.10

ApplicationWindow { 
    property string accent1color: "#144F85"
    property string backgroundcolor: "#141414"
    property string backgroundcolor2: "#242424"
    property string textColor: "#FFFFFF"
    
    title: "StatiCAN"

    id: root
    width: 800
    height: 600

    visible: true
    color: backgroundcolor

    Rectangle {
        id: stati_Rect

        anchors {
            top:parent.top
            left: parent.left
            topMargin: 15
            leftMargin: 15
        }

        width: 90
        height: 55
        color: "transparent"
        radius: 10
        border.width: 0

        Text {
            id: text1
            color: "#18458b"
            text: qsTr("Stati")
            anchors.fill: parent
            font.pixelSize: 40
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.bold: true
        }
    }

    Rectangle {
        id: can_Rect

        anchors {
            top: parent.top
            left: stati_Rect.right
            topMargin:15
        }

        width: 95
        height: 55
        color: "#18458b"
        radius: 10
        border.width: 0

        Text {
            id: can_txt
            color: "#ffffff"
            text: qsTr("CAN")
            anchors.fill: parent
            font.pixelSize: 40
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.bold: true
        }
    }

    Rectangle {
        id: separatorBar
        color: "#1A1A1A"

        width: 3

        anchors {
            top: parent.top
            bottom: parent.bottom
            left: can_Rect.right

            topMargin: 15
            bottomMargin: 15
            leftMargin: 12
        }
    }

    Rectangle {
        id: rectangle2
        color: "transparent" 
        radius: 10

        anchors {
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            left: separatorBar.right
            rightMargin: 15
            topMargin: 15
            bottomMargin: 25
            leftMargin: 8
        }
        z: 1

        Rectangle {
            id: filler
            anchors.fill: parent
            anchors.margins: 3
            color: backgroundcolor

            Component {
                id: savedDelegate
                Item {
                    id: savedItem
                    width: parent.width; height: 40
                    Rectangle {
                        anchors.fill: parent
                        Text {
                            anchors {
                                right: parent.right
                                top: parent.top
                                rightMargin: 5
                                topMargin: 5
                            }


                        }
                    }
                }
            }

            ListModel {
                id: savedModel
                // example dummy objects, delete later
                ListElement {
                    file_name: "car_scanner.ino"
                    issues: 0
                }
                ListElement {
                    file_name: "can_sender.ino"
                    issues: 2
                }
                ListElement {
                    file_name: "random_example.ino"
                    issues: 2
                }
                ListElement {
                    file_name: "test.ino"
                    issues: 5
                }
                ListElement {
                    file_name: "can_handler.ino"
                    issues: 0
                }
                ListElement {
                    file_name: "can_read_write.ino"
                    issues: 1
                }
            }

            ListView {
                id: savedList
                anchors.fill: parent
                orientation: Qt.Vertical
                model: savedModel
                boundsBehavior: Flickable.StopAtBounds
                clip: true
                
                delegate: Item {
                    width: parent.width; height: 120
                    RectangularShadow {
                        anchors.fill: delegateRect
                        radius: delegateRect.radius
                        offset.x: 5 
                        offset.y: 5
                        blur: 8 // Shadow softness
                        spread: 0 // Shadow size relative to source
                        color: '#80000000' // Shadow color with alpha 
                        antialiasing: true // Smooth the edges
                    }
                    
                    Rectangle {
                        id: delegateRect
                        anchors {
                            fill: parent
                            margins: 8
                        }

                        color: backgroundcolor2
                        radius: 10

                        Text {
                            anchors {
                                left: parent.left
                                top: parent.top
                                leftMargin: 10
                                topMargin: 10
                            }

                            text: file_name
                            font.pixelSize: 30
                            color: textColor
                        }

                        Image {
                            id: symbol_img
                            anchors {
                                left: parent.left
                                bottom: parent.bottom
                                leftMargin: 10
                                bottomMargin: 8
                            }

                            source: {
                                if(issues === 0) {"./assets/checkmark_icon.png"}
                                else {"./assets/x_icon.png"}
                            }
                        }

                        Text {
                            anchors {
                                left: symbol_img.right
                                bottom: parent.bottom
                                leftMargin: 8
                                bottomMargin: 12
                            }

                            text: {
                                if(issues === 0) {"No issues found"}
                                else if(issues === 1 ) {"1 issue found"}
                                else (issues + " issues found")
                            }
                            
                            font.pixelSize: 26
                            color:  "#969696" //issues === 0 ? '#00ff77' : "#FF0000"
                        }

                        Button {
                            id: accessElement
                            anchors.fill: parent
                            //enabled: isFocused
                            flat: true

                            /*
                            background: Rectangle {
                                //implicitWidth: parent.width
                                //implicitHeight: parent.height
                                color: "transparent"
                            }
                            */

                            HoverHandler { cursorShape: Qt.PointingHandCursor }

                            onClicked: { 
                               //add functionality here
                            }
                        }
                    }
                }
            }

            Text {
                id: placeholderListText
                anchors.centerIn: parent
                horizontalAlignment: Text.AlignHCenter
                text: "Scanned files will appear here. Click the '+' icon to upload a file."
                font.pixelSize: 16
                color: textColor
                visible: savedList.count === 0 ? true : false
            }
        }
    }

    Rectangle {
        id: topShadowRect
         anchors {
            top: rectangle2.top
            left: rectangle2.left
            right: rectangle2.right
        }
        height: parent.height - rectangle2.height - 8
        radius: 5
        z:3
        gradient: Gradient {
            GradientStop { position: 0.0; color:  '#80000000' } 
            GradientStop { position: 1.0; color:  '#00000000' }
        }
        visible: savedList.atYBeginning === true ? false : true
    }

    Rectangle {
        id: bottomShadowRect
        anchors {
            bottom: rectangle2.bottom
            left: rectangle2.left
            right: rectangle2.right
        }

        height: parent.height - rectangle2.height - 8
        radius: 5
        z:3
        gradient: Gradient {
            GradientStop { position: 0.0; color:  '#00000000' } // Start color at the top (0.0)
            GradientStop { position: 1.0; color:  '#80000000' }
        }
        visible: savedList.atYEnd === true ? false : true
    }

    /*
    RectangularShadow {
        anchors.fill: topShadowRect
        offset.x: 5 
        offset.y: 0 
        radius:topShadowRect.radius
        blur: 20 // Shadow softness
        spread: 0 // Shadow size relative to source
        color: '#805B5B5B' // Shadow color with alpha (black, 50% opacity)
        antialiasing: true // Smooth the edges
        z:1
        visible: savedList.atYBeginning === true ? false : true
    }

    Rectangle {
        id: topShadowRect
        anchors {
            bottom: rectangle2.top
            left: rectangle2.left
            right: parent.right
            top:parent.top
        }
        z:2
        color: backgroundcolor
    }

    RectangularShadow {
        anchors.fill: bottomShadowRect
        offset.x: 5 
        offset.y: 0 
        radius:topShadowRect.radius
        blur: 30 // Shadow softness
        spread: 0 // Shadow size relative to source
        color: '#805b5b5b' // Shadow color with alpha (black, 50% opacity)
        antialiasing: true // Smooth the edges
        z:1
        visible: savedList.atYEnd === true ? false : true
    }

    Rectangle {
        id: bottomShadowRect
        anchors {
            bottom: parent.bottom
            left: rectangle2.left
            right: parent.right
            top: rectangle2.bottom
        }
        z:2
        color: backgroundcolor
    }
    */


    RectangularShadow {
        anchors.fill: help_rect
        offset.x: 5 
        offset.y: 5 
        radius: upload_file_rect.radius
        blur: 20 // Shadow softness
        spread: 0 // Shadow size relative to source
        color: "#80000000" // Shadow color with alpha (black, 50% opacity)
        antialiasing: true // Smooth the edges
    }

    Rectangle {
        id: help_rect
        width: 90
        height: 90
        color: "#18458b"
        radius: 45

        anchors {
            left: parent.left
            bottom: settings_rect.top
            leftMargin: 25
            bottomMargin: 25
        }
        z: 1

        Text {
            anchors {
                top: parent.top
                bottom: parent.bottom
                right:parent.right
                left: parent.left
                
                topMargin: 8
                bottomMargin: 12
                leftMargin: 10
                rightMargin: 10
            }

            text: "?"
            font.pixelSize: 70
            font.bold: true
            color: "#FFFFFF"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }

        RoundButton {
            id: button_help
            anchors.fill: parent
            radius: 45
            flat: true

            HoverHandler { 
                id: buttonHoverHelp
                cursorShape: Qt.PointingHandCursor 
            }

            ToolTip {
                id: helpToolTip
                visible: buttonHoverHelp.hovered
                text: "Help"
                delay: 500

                contentItem: Text {
                    text: helpToolTip.text
                    color: textColor
                }

                background: Rectangle {
                    color: backgroundcolor
                    border.color: accent1color
                    radius: 5
                }
            }
        }
    }

    RectangularShadow {
        anchors.fill: settings_rect
        offset.x: 5 
        offset.y: 5 
        radius: upload_file_rect.radius
        blur: 20 // Shadow softness
        spread: 0 // Shadow size relative to source
        color: "#80000000" // Shadow color with alpha (black, 50% opacity)
        antialiasing: true // Smooth the edges
    }

    Rectangle {
        id: settings_rect
        width: 90
        height: 90
        color: "#18458b"
        radius: 45

        anchors {
            left: parent.left
            bottom: upload_file_rect.top
            leftMargin: 25
            bottomMargin: 25
        }
        z: 1

        Image {
            id: settings_img
            anchors.centerIn: parent
            source: "./assets/settings_edit.png"
        }

        /*
        Text {
            anchors {
                top: parent.top
                bottom: parent.bottom
                right:parent.right
                left: parent.left
                
                topMargin: 8
                bottomMargin: 12
                leftMargin: 10
                rightMargin: 10
            }

            text: "⛭"
            font.pixelSize: 70
            font.bold: true
            color: "#FFFFFF"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
       
        Rectangle {
            anchors.centerIn: parent
            width: 20
            height: 20
            radius: 10
            color: "#FFFFFF"
        }
        */
        
        RoundButton {
            id: button_settings
            anchors.fill: parent
            radius: 45
            flat: true

            HoverHandler { 
                id: buttonHoverSettings
                cursorShape: Qt.PointingHandCursor 
            }

            ToolTip {
                id: settingsToolTip
                visible: buttonHoverSettings.hovered
                text: "Settings"
                delay: 500

                contentItem: Text {
                    text: settingsToolTip.text
                    color: textColor
                }

                background: Rectangle {
                    color: backgroundcolor
                    border.color: accent1color
                    radius: 5
                }
            }
        }
    }

    RectangularShadow {
        anchors.fill: upload_file_rect
        offset.x: 5 
        offset.y: 5 
        radius: upload_file_rect.radius
        blur: 20 // Shadow softness
        spread: 0 // Shadow size relative to source
        color: "#80000000" // Shadow color with alpha (black, 50% opacity)
        antialiasing: true // Smooth the edges
    }

    Rectangle {
        id: upload_file_rect
        width: 90
        height: 90
        color: "#18458b"
        radius: 45

        anchors {
            left: parent.left
            bottom: parent.bottom
            leftMargin: 25
            bottomMargin: 25
        }
        z: 1

        RoundButton {
            id: button
            anchors.fill: parent
            radius: 45
            flat: true

            HoverHandler { 
                id: buttonHoverUpload
                cursorShape: Qt.PointingHandCursor 
            }

            ToolTip {
                id: uploadToolTip
                visible: buttonHoverUpload.hovered
                text: "Upload File"
                delay: 500

                contentItem: Text {
                    text: uploadToolTip.text
                    color: textColor
                }

                background: Rectangle {
                    color: backgroundcolor
                    border.color: accent1color
                    radius: 5
                }
            }
        }

        Rectangle {
            id: rectangle4
            width: 10
            height: 60
            color: "#ffffff"
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Rectangle {
            id: rectangle5
            width: 10
            height: 60
            color: "#ffffff"
            anchors.verticalCenter: parent.verticalCenter
            rotation: 90
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    // NOT CONNECTED TO ANYTHING YET //
    function switchColorMode() {
        if(backgroundcolor == "#FFFFFF") {
            backgroundcolor = "#141414"
            backgroundcolor2 = "#242424"
            textColor = "#FFFFFF"
        }
        else {
            backgroundcolor = "#FFFFFF"
            backgroundcolor2 = "#D0D0D0"
            textColor = "#000000"
        }
    }
}
