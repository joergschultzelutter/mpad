#
# Multi-Purpose APRS Daemon: Funstuff Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Magic-8-ball routine which is mainly used for UTF-8 outpit and
# language selection testing. Nevertheless, it still might be able
# to preduct your future - so I decided to keep it after the test
# got completed :-)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import logging

lang_en_fortunes = [
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes – definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Reply hazy, try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
]

lang_de_fortunes = [
    "Es ist sicher",
    "Es ist eindeutig so",
    "Zweifelsfrei",
    "Ja - definitiv",
    "Du kannst Dich darauf verlassen",
    "So wie ich es sehe: ja",
    "Sehr wahrscheinlich",
    "Meine Prognose ist: gut",
    "Ja",
    "Alle Zeichen sagen: ja",
    "Antwort unklar; versuche es noch einmal",
    "Frag mich später noch einmal",
    "Ich verrate es Dir besser jetzt noch nicht",
    "Vorhersage derzeit nicht möglich",
    "Konzentriere Dich und frage mich nochmals",
    "Verlass Dich nicht darauf",
    "Meine Antwort ist nein",
    "Meine Prognose ist: nicht gut",
    "Sehr zweifelhaft",
]

lang_es_fortunes = [
    "En mi opinión, sí",
    "Es cierto",
    "Es decididamente así",
    "Probablemente",
    "Buen pronóstico",
    "Todo apunta a que sí",
    "Sin duda",
    "Sí",
    "Sí - definitivamente",
    "Debes confiar en ello",
    "Respuesta vaga, vuelve a intentarlo",
    "Pregunta en otro momento",
    "Será mejor que no te lo diga ahora",
    "No puedo predecirlo ahora",
    "Concéntrate y vuelve a preguntar",
    "No cuentes con ello",
    "Mi respuesta es no",
    "Mis fuentes me dicen que no",
    "Las perspectivas no son buenas",
    "Muy dudoso",
]

lang_fr_fortunes = [
    "D'après moi oui",
    "C'est certain",
    "Oui absolument",
    "Tu peux compter dessus",
    "Sans aucun doute",
    "Très probable",
    "Oui",
    "C'est bien parti",
    "Essaye plus tard",
    "Essaye encore",
    "Pas d'avis",
    "C'est ton destin",
    "Le sort en est jeté",
    "Une chance sur deux",
    "Repose ta question",
    "C'est non",
    "Peu probable",
    "Faut pas rêver",
    "N'y compte pas",
    "Impossible",
]

lang_it_fortunes = [
    "Per quanto posso vedere, sì",
    "È certo",
    "È decisamente così",
    "Molto probabilmente",
    "Le prospettive sono buone",
    "I segni indicano di sì",
    "Senza alcun dubbio",
    "Sì",
    "Sì, senza dubbio",
    "Ci puoi contare",
    "È difficile rispondere, prova di nuovo",
    "Rifai la domanda più tardi",
    "Meglio non risponderti adesso",
    "Non posso predirlo ora",
    "Concentrati e rifai la domanda",
    "Non ci contare",
    "La mia risposta è no",
    "Le mie fonti dicono di no",
    "Le prospettive non sono buone",
    "Molto incerto",
]






if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)