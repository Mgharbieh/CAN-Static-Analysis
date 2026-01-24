import QtQuick 6.10
import QtQuick.Controls 6.10

Item {
    id: root
    width: 40
    height: 40

    property color arcColor: "#2196F3"   // Blue
    property real arcWidth: 4
    property real arcLength: Math.PI * 1.2
    property int duration: 1000
    property bool isRunning
    visible: isRunning

    Canvas {
        id: canvas
        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            var r = Math.min(width, height) / 2 - arcWidth
            var cx = width / 2
            var cy = height / 2

            ctx.save()
            ctx.translate(cx, cy)
            ctx.rotate(rotationAngle)

            ctx.beginPath()
            ctx.strokeStyle = arcColor
            ctx.lineWidth = arcWidth
            ctx.lineCap = "round"
            ctx.arc(0, 0, r, 0, arcLength)
            ctx.stroke()

            ctx.restore()
        }

        property real rotationAngle: 0

        Timer {
            running: root.isRunning
            repeat: true
            interval: 16   // ~60 FPS
            onTriggered: {
                canvas.rotationAngle += (2 * Math.PI) / (duration / interval)
                canvas.requestPaint()
            }
        }
    }
}