#by T.Hayashi
#tested with Python3.7, pyparsing 2.4.6
#don't use full-width space as delimitter in this script.
from pyparsing import (
       Combine as 結合,
       Word as 列,
       nums as 数字,
       __version__ as 版数,
       Regex ,
       pyparsing_unicode as uni,
       ParseException)

#以下日本語
def 文法を定義():

    後方一致 = lambda s : Regex(r'.*'+s)

    整数 = 列(数字)
    漢字列 = 列(uni.Japanese.Kanji.alphas)
    かな列 = 列(uni.Japanese.Hiragana.alphas)

    会員番号 = 整数('会員番号')

    姓名 = 漢字列('姓名')
    姓名読み = かな列('姓名読み')

    会社名前方 = 結合('株式会社' + 漢字列)
    会社名 = 会社名前方 | 後方一致('会社')
    代表者 = 漢字列('代表者')
    賛助会員 = (会社名 + 代表者 + 会員番号)('賛助会員')

    学校名 = 後方一致('大学') | 後方一致('高専') | 後方一致('大学校')
    学生会員 = (学校名 + 姓名 + 姓名読み + 会員番号)('学生会員')

    個人会員 = (姓名 + 姓名読み + 会員番号)('個人会員')

    協会員 = 賛助会員 | 学生会員 | 個人会員
    return 協会員

def テスト(gram,instr):
    try:
        r=gram.parseString(instr)
        name=r.getName()
        print(name,r.get(name))
        print()
    except ParseException as pe:
        print(f'error at {pe.loc} of {instr}')
        print(instr)
        #loc : char position.
        print('　'*(pe.loc-2)+'^')
        #print('Explain:\n',ParseException.explain(pe))


print('pyparsing 版数:',版数)       
文法=文法を定義()

テスト(文法,'山田太郎 やまだたろう 3456')
テスト(文法,'架空東大学 川崎三郎 かわさきさぶろう 5127')
テスト(文法,'株式会社架空商事 東太郎 0015') #前方一致
テスト(文法,'架空商事株式会社 海山太郎 0010') #後方一致
テスト(文法,'北北西高専 伊藤一郎 いとういちろう 900')
#エラーの確認　高校は定義に無い
テスト(文法,'北北東高校 鈴木三郎 すずきさぶろう 1000')
#エラーの確認　会社が抜け
テスト(文法,'株式架空商事 東太郎 0015')
#エラーの確認　読みに漢字
テスト(文法,'山田一太郎 やまだ一太郎 3456')
