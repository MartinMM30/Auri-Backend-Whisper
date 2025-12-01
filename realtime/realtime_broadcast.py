# realtime/realtime_broadcast.py

class RealtimeBroadcaster:
    def __init__(self):
        self.connections = set()

    # Cada cliente WS se registra aquí
    def register(self, ws):
        self.connections.add(ws)

    # Cuando un cliente cierra conexión
    def unregister(self, ws):
        if ws in self.connections:
            self.connections.remove(ws)

    # Enviar evento a TODOS los WS conectados
    async def broadcast(self, msg: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(msg)
            except:
                dead.append(ws)

        for ws in dead:
            self.unregister(ws)


# instancia global
realtime_broadcast = RealtimeBroadcaster()
