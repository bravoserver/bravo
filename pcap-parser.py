import dpkt
import sys
import socket
from bravo.beta.packets import parse_packets, hexout
from bravo.beta.protocol import clientbound, serverbound
from bravo.beta.encryption import BravoCryptRSA, BravoCryptAES
from Crypto.PublicKey import RSA

# This data was filtered via "tcp.port==25565"


class PcapParser:
    packet_list = []
    streams = {}
    client = ''
    server = ''
    mode = 'handshaking'
    index = 0
    cryptRSA = None
    cryptAES = None

    def __init__(self, filename):
        f = open(filename)
        pcap = dpkt.pcap.Reader(f)
        self.packet_list = [(ts, buf) for ts, buf in pcap]
        f.close()
        # JMT: hardcode for now
        with open('/home/jmt/bravo-key/server_id_rsa.pub') as f:
            public_key = RSA.importKey(f.read())
        with open('/home/jmt/bravo-key/server_id_rsa') as f:
            private_key = RSA.importKey(f.read())
        server_id = 'x' * 20
        self.cryptRSA = BravoCryptRSA(public_key=public_key, private_key=private_key, server_id=server_id)

    def __call__(self):
        for envelope in self.packet_list:
            buf = envelope[1]
            eth = dpkt.ethernet.Ethernet(buf)
            ip = eth.data
            src = socket.inet_ntoa(ip.src)
            dst = socket.inet_ntoa(ip.dst)
            if self.client == '':
                self.client = src
            else:
                if self.server == '':
                    self.server = src
            if src == self.client:
                streamkey = 'client'
                packetdict = serverbound
            else:
                streamkey = 'server'
                packetdict = clientbound
            tcp = ip.data
            mydata = tcp.data
            if mydata == '':
                continue
            # Decryption!
            if self.cryptAES is not None:
                mydata = stream_decrypt(mydata)
            try:
                self.streams[streamkey] += mydata
            except KeyError:
                self.streams[streamkey] = mydata
            packets, self.streams[streamkey] = parse_packets(self.streams[streamkey])
            for header, payload in packets:
                if header in packetdict[self.mode]:
                    struct = packetdict[self.mode][header]
                    name = 'handle_%s_sent_%s' % (streamkey, struct.name)
                    if payload == '':
                        inner_packet = ''
                    else:
                        try:
                            inner_packet = struct.parse(payload)
                        except Exception as e:
                            print e, header, payload
                    self.index += 1
                    try:
                        getattr(self, name)(inner_packet)
                    except AttributeError:
                        print "Need to write %s method!" % name

    # serverbound packets
    def handle_client_sent_handshaking(self, packet):
        self.mode = packet.next_state

    def handle_client_sent_encryption_response(self, packet):
        self.shared_secret = self.cryptRSA.decrypt(packet.secret)

    def handle_client_sent_login_start(self, packet):
        pass

    def handle_client_sent_status_request(self, packet):
        pass

    def handle_client_sent_status_ping(self, packet):
        pass

    def handle_client_sent_keepalive(self, packet):
        pass

    def handle_client_sent_chat(self, packet):
        pass

    def handle_client_sent_use_entity(self, packet):
        pass

    def handle_client_sent_player(self, packet):
        pass

    def handle_client_sent_player_position(self, packet):
        pass

    def handle_client_sent_player_look(self, packet):
        pass

    def handle_client_sent_player_position_and_look(self, packet):
        pass

    def handle_client_sent_player_digging(self, packet):
        pass

    def handle_client_sent_player_block_placement(self, packet):
        pass

    def handle_client_sent_held_item_change(self, packet):
        pass

    def handle_client_sent_animation(self, packet):
        pass

    def handle_client_sent_entity_action(self, packet):
        pass

    def handle_client_sent_steer_vehicle(self, packet):
        pass

    def handle_client_sent_close_window(self, packet):
        pass

    def handle_client_sent_click_window(self, packet):
        pass

    def handle_client_sent_confirm_transaction(self, packet):
        pass

    def handle_client_sent_creative_inventory_action(self, packet):
        pass

    def handle_client_sent_enchant_item(self, packet):
        pass

    def handle_client_sent_update_sign(self, packet):
        pass

    def handle_client_sent_player_abilities(self, packet):
        pass

    def handle_client_sent_tab(self, packet):
        pass

    def handle_client_sent_client_settings(self, packet):
        pass

    def handle_client_sent_client_status(self, packet):
        pass

    def handle_client_sent_plugin_message(self, packet):
        pass

    # clientbound packets
    def handle_server_sent_handshaking(self, packet):
        pass

    def handle_server_sent_encryption_request(self, packet):
        pass

    def handle_server_sent_disconnect(self, packet):
        pass

    def handle_server_sent_status_response(self, packet):
        pass

    def handle_server_sent_status_ping(self, packet):
        self.mode = 'handshaking'

    def handle_server_sent_login_success(self, packet):
        self.mode = 'play'

    def handle_server_sent_keepalive(self, packet):
        pass

    def handle_server_sent_join(self, packet):
        pass

    def handle_server_sent_chat(self, packet):
        pass

    def handle_server_sent_time(self, packet):
        pass

    def handle_server_sent_entity_equipment(self, packet):
        pass

    def handle_server_sent_spawn_position(self, packet):
        pass

    def handle_server_sent_update_health(self, packet):
        pass

    def handle_server_sent_respawn(self, packet):
        pass

    def handle_server_sent_player_position_and_look(self, packet):
        pass

    def handle_server_sent_held_item(self, packet):
        pass

    def handle_server_sent_use_bed(self, packet):
        pass

    def handle_server_sent_animation(self, packet):
        pass

    def handle_server_sent_spawn_player(self, packet):
        pass

    def handle_server_sent_collect_item(self, packet):
        pass

    def handle_server_sent_spawn_object(self, packet):
        pass

    def handle_server_sent_spawn_mob(self, packet):
        pass

    def handle_server_sent_spawn_painting(self, packet):
        pass

    def handle_server_sent_spawn_experience_orb(self, packet):
        pass

    def handle_server_sent_entity_velocity(self, packet):
        pass

    def handle_server_sent_destroy_entities(self, packet):
        pass

    def handle_server_sent_create_entity(self, packet):
        pass

    def handle_server_sent_entity_relative_move(self, packet):
        pass

    def handle_server_sent_entity_look(self, packet):
        pass

    def handle_server_sent_entity_look_and_relative_move(self, packet):
        pass

    def handle_server_sent_entity_teleport(self, packet):
        pass

    def handle_server_sent_entity_head_look(self, packet):
        pass

    def handle_server_sent_entity_status(self, packet):
        pass

    def handle_server_sent_attach_entity(self, packet):
        pass

    def handle_server_sent_entity_metadata(self, packet):
        pass

    def handle_server_sent_entity_effect(self, packet):
        pass

    def handle_server_sent_entity_remove_effect(self, packet):
        pass

    def handle_server_sent_set_experience(self, packet):
        pass

    def handle_server_sent_entity_properties(self, packet):
        pass

    def handle_server_sent_chunk_data(self, packet):
        pass

    def handle_server_sent_multi_block_change(self, packet):
        pass

    def handle_server_sent_block_change(self, packet):
        pass

    def handle_server_sent_block_action(self, packet):
        pass

    def handle_server_sent_block_break_animation(self, packet):
        pass

    def handle_server_sent_map_chunk_bulk(self, packet):
        pass

    def handle_server_sent_explosion(self, packet):
        pass

    def handle_server_sent_effect(self, packet):
        pass

    def handle_server_sent_sound_effect(self, packet):
        pass

    def handle_server_sent_particle(self, packet):
        pass

    def handle_server_sent_change_game_state(self, packet):
        pass

    def handle_server_sent_spawn_global_entity(self, packet):
        pass

    def handle_server_sent_open_window(self, packet):
        pass

    def handle_server_sent_close_window(self, packet):
        pass

    def handle_server_sent_set_slot(self, packet):
        pass

    def handle_server_sent_window_items(self, packet):
        pass

    def handle_server_sent_window_property(self, packet):
        pass

    def handle_server_sent_confirm_transaction(self, packet):
        pass

    def handle_server_sent_update_sign(self, packet):
        pass

    def handle_server_sent_maps(self, packet):
        pass

    def handle_server_sent_update_block_entity(self, packet):
        pass

    def handle_server_sent_sign_editor_open(self, packet):
        pass

    def handle_server_sent_statistics(self, packet):
        pass

    def handle_server_sent_player_list_item(self, packet):
        pass

    def handle_server_sent_player_abilities(self, packet):
        pass

    def handle_server_sent_tab_complete(self, packet):
        pass

    def handle_server_sent_scoreboard_objective(self, packet):
        pass

    def handle_server_sent_update_score(self, packet):
        pass

    def handle_server_sent_display_scoreboard(self, packet):
        pass

    def handle_server_sent_teams(self, packet):
        pass

    def handle_server_sent_plugin_message(self, packet):
        pass


class InventoryAnalyzer(PcapParser):
    def handle_client_sent_use_entity(self, packet):
        PcapParser.handle_client_sent_use_entity(self, packet)
        print "%d: Client sent use entity: %s" % (self.index, packet)

    def handle_client_sent_held_item_change(self, packet):
        PcapParser.handle_client_sent_held_item_change(self, packet)
        print "%d: Client sent held item change: %s" % (self.index, packet)

    def handle_client_sent_player_block_placement(self, packet):
        PcapParser.handle_client_sent_player_block_placement(self, packet)
        print "%d: Client sent player block placement: %s" % (self.index, packet)

    def handle_client_sent_entity_action(self, packet):
        PcapParser.handle_client_sent_entity_action(self, packet)
        print "%d: Client sent entity action: %s" % (self.index, packet)

    def handle_client_sent_close_window(self, packet):
        PcapParser.handle_client_sent_close_window(self, packet)
        print "%d: Client sent close window: %s" % (self.index, packet)

    def handle_client_sent_click_window(self, packet):
        PcapParser.handle_client_sent_click_window(self, packet)
        print "%d: Client sent click window: %s" % (self.index, packet)

    def handle_client_sent_confirm_transaction(self, packet):
        PcapParser.handle_client_sent_confirm_transaction(self, packet)
        print "%d: Client sent confirm transaction: %s" % (self.index, packet)

    def handle_client_sent_creative_inventory_action(self, packet):
        PcapParser.handle_client_sent_creative_inventory_action(self, packet)
        print "%d: Client sent creative inventory action: %s" % (self.index, packet)

    def handle_server_sent_held_item(self, packet):
        PcapParser.handle_server_sent_held_item(self, packet)
        print "%d: Server sent held item: %s" % (self.index, packet)

    def handle_server_sent_collect_item(self, packet):
        PcapParser.handle_server_sent_collect_item(self, packet)
        print "%d: Server sent collect item: %s" % (self.index, packet)

    def handle_server_sent_open_window(self, packet):
        PcapParser.handle_server_sent_open_window(self, packet)
        print "%d: Server sent open window: %s" % (self.index, packet)

    def handle_server_sent_close_window(self, packet):
        PcapParser.handle_server_sent_close_window(self, packet)
        print "%d: Server sent close window: %s" % (self.index, packet)

    def handle_server_sent_set_slot(self, packet):
        PcapParser.handle_server_sent_set_slot(self, packet)
        print "%d: Server sent set slot: %s" % (self.index, packet)

    def handle_server_sent_window_items(self, packet):
        PcapParser.handle_server_sent_window_items(self, packet)
        print "%d: Server sent window items: %s" % (self.index, packet)

    def handle_server_sent_window_property(self, packet):
        PcapParser.handle_server_sent_window_property(self, packet)
        print "%d: Server sent window property: %s" % (self.index, packet)

    def handle_server_sent_confirm_transaction(self, packet):
        PcapParser.handle_server_sent_confirm_transaction(self, packet)
        print "%d: Server sent confirm transaction: %s" % (self.index, packet)

    def handle_server_sent_spawn_object(self, packet):
        PcapParser.handle_server_sent_spawn_object(self, packet)
        print "%d: Server sent spawn object: %s" % (self.index, packet)

    def handle_server_sent_entity_metadata(self, packet):
        PcapParser.handle_server_sent_entity_metadata(self, packet)
        print "%d: Server sent entity metadata: %s" % (self.index, packet)


class EncryptionAnalyzer(PcapParser):
    def handle_client_sent_encryption_response(self, packet):
        PcapParser.handle_client_sent_encryption_response(self, packet)
        print "%d: Client sent encryption response: %s" % (self.index, packet)

    def handle_server_sent_encryption_request(self, packet):
        PcapParser.handle_server_sent_encryption_request(self, packet)
        print "%d: Server sent encryption request: %s" % (self.index, packet)

    def handle_server_sent_join(self, packet):
        PcapParser.handle_server_sent_join(self, packet)
        print "%d: Server sent join: %s" % (self.index, packet)

    def handle_client_sent_client_settings(self, packet):
        PcapParser.handle_client_sent_client_settings(self, packet)
        pass


#p = InventoryAnalyzer(sys.argv[1])
p = EncryptionAnalyzer(sys.argv[1])
p()
