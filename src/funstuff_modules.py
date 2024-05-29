#
# Multi-Purpose APRS Daemon: Funstuff Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Magic-8-ball routine which is mainly used for UTF-8 output and
# language selection testing. Nevertheless, it still might be able
# to preduct YOUR future :-) - so I decided to keep it after the test
# got completed. Localised Magic 8 ball answers have been taken from
# my source of wisdom (Wikipedia)
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
import random

lang_en_fortunes = (
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
)

lang_de_fortunes = (
    "Es ist sicher",
    "Es ist eindeutig so",
    "Zweifelsfrei",
    "Ja - definitiv",
    "Du kannst Dich darauf verlassen",
    "So wie ich es sehe: ja",
    "Sehr wahrscheinlich",
    "Meine Prognose sagt: ja",
    "Ja",
    "Alle Zeichen sagen: ja",
    "Antwort unklar; versuche es noch einmal",
    "Frag mich später noch einmal",
    "Das verrate ich Dir besser jetzt noch nicht",
    "Vorhersage derzeit nicht möglich",
    "Konzentriere Dich und frage mich nochmals",
    "Verlass Dich nicht darauf",
    "Meine Antwort ist nein",
    "Meine Quellen sagen: nein",
    "Meine Prognose sagt: nicht gut",
    "Sehr zweifelhaft",
)

lang_es_fortunes = (
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
)

lang_fr_fortunes = (
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
)

lang_it_fortunes = (
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
)

lang_nl_fortunes = (
    "Het is zeker",
    "Het is beslist zo",
    "Zonder twijfel",
    "Zeer zeker",
    "Je kunt erop vertrouwe",
    "Volgens mij wel",
    "Zeer waarschijnlijk",
    "Goed vooruitzicht",
    "Ja",
    "Tekenen wijzen op ja",
    "Reactie is wazig, probeer opnieuw",
    "Vraag later opnieuw",
    "Beter je nu niet te zeggen",
    "Niet nu te voorspellen",
    "Concentreer je en vraag opnieuw",
    "Reken er niet op",
    "Mijn antwoord is nee",
    "Mijn bronnen zeggen nee",
    "Vooruitzicht is niet zo goed",
    "Zeer twijfelachtig",
)

lang_ru_fortunes = (
    "Бесспорно",
    "Предрешено",
    "Никаких сомнений",
    "Определённо да",
    "Можешь быть уверен в этом",
    "Мне кажется: да",
    "Вероятнее всего",
    "Хорошие перспективы",
    "Знаки говорят — да",
    "Да",
    "Пока не ясно, попробуй снова",
    "Спроси позже",
    "Лучше не рассказывать",
    "Сейчас нельзя предсказать",
    "Сконцентрируйся и спроси опять",
    "Даже не думай",
    "Мой ответ — нет",
    "По моим данным — нет",
    "Перспективы не очень хорошие",
    "Весьма сомнительно",
)

lang_tr_fortunes = (
    "Kesinlikle",
    "Kesinlikle öyle",
    "Kuşkusuz",
    "Evet - elbette",
    "Bana güvenebilirsin",
    "Gördüğüm kadarıyla, evet",
    "Çoğunlukla",
    "Dışarıdan iyi görünüyor",
    "Evet",
    "Belirtiler olduğu yönünde",
    "Biraz belirsiz, tekrar dene",
    "Sonra tekrar dene",
    "Şimdi söylemesem daha iyi",
    "Şimdi kehanette bulunamam",
    "Konsantre ol ve tekrar sor",
    "Bana öyle bakma",
    "Yanıtım hayır",
    "Kaynaklarım hayır diyor",
    "Pek iyi görünmüyor",
    "Çok şüpheli",
)

lang_cn_fortunes = (
    "這是必然",
    "肯定是的",
    "不用懷疑",
    "毫無疑問",
    "你能依靠它",
    "如我所見，是的",
    "很有可能",
    "外表很好",
    "是的",
    "種種跡象指出:是的",
    "回覆攏統，再試試",
    "待會再問",
    "最好現在不告訴你",
    "現在無法預測",
    "專心再問一遍",
    "想的美",
    "我的回覆是:不",
    "我的來源說:不",
    "外表不太好",
    "很可疑",
)

lang_pl_fortunes = (
    "To pewne",
    "Zdecydowanie tak",
    "Bez wątpienia",
    "Tak - zdecydowanie",
    "Możesz na tym polegać",
    "Tak, jak ja to widzę",
    "Najprawdopodobniej",
    "Perspektywa dobra",
    "Tak",
    "Znaki wskazujące na tak",
    "Odpowiedź niewyraźna, spróbuj ponownie",
    "Zapytaj ponownie później",
    "Lepiej ci teraz nie mówić",
    "Nie mogę teraz przewidzieć",
    "Skoncentruj się i zapytaj ponownie",
    "Nie licz na to",
    "Moja odpowiedź brzmi: nie",
    "Według moich źródeł, nie",
    "Perspektywa niezbyt dobra",
    "Bardzo wątpliwe",
)

lang_hr_fortunes = (
    "Sigurno je",
    "To je definitivno tako",
    "Bez sumnje",
    "Da definitivno",
    "Možete se osloniti na to",
    "Koliko vidim, da",
    "Najvjerojatnije",
    "Outlook dobar",
    "Da",
    "Znakovi upućuju na da",
    "Odgovorite maglovito, pokušajte ponovo",
    "Pitajte ponovo kasnije",
    "Bolje da ti sada ne kažem",
    "Ne mogu sada predvidjeti",
    "Koncentrirajte se i pitajte ponovno",
    "Ne računajte na to",
    "Moj odgovor je ne",
    "Moji izvori kažu ne",
    "Outlook nije tako dobar",
    "Vrlo sumnjivo",
)


fortunes_dictionary = {
    "en": lang_en_fortunes,
    "de": lang_de_fortunes,
    "es": lang_es_fortunes,
    "fr": lang_fr_fortunes,
    "it": lang_it_fortunes,
    "nl": lang_nl_fortunes,
    "ru": lang_ru_fortunes,
    "tr": lang_tr_fortunes,
    "cn": lang_cn_fortunes,
    "pl": lang_pl_fortunes,
    "hr": lang_hr_fortunes,
}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_fortuneteller_message(language: str = "en"):
    """
    This is a standard "fortune cookie" / Magic 8 Ball generator
    where some of the answers exist in localised formats. Apart
    from returning Unicode/localised content, it does not do
    anything useful

    Parameters
    ==========
    language : 'str'
        ISO639-a2 language code

    Returns
    =======
    fortune: 'str'
        localised magic 8 ball / fortune cookie string
    """

    if language in fortunes_dictionary:
        lang_fortunes = fortunes_dictionary[language]
    else:
        lang_fortunes = fortunes_dictionary["en"]

    value = random.randint(0, len(lang_fortunes) - 1)
    return lang_fortunes[value]


if __name__ == "__main__":
    pass
