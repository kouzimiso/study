import TextControl
def main():
    default_settings = {
        "source_code":"""
    
Sub A1モトメール()

'温度ｶｻﾈｰﾙver.1
'2015.06.23 平均ﾓﾄﾒｰﾙを修正して作成開始

'sheet(1)=温度ｶｻﾈｰﾙ

'sheet(2)=A1ｶｻﾈｰﾙ
'sheet(3)=A2ｶｻﾈｰﾙ
'sheet(4)=A3ｶｻﾈｰﾙ
'sheet(5)=A4ｶｻﾈｰﾙ

'sheet(6)=A1_T_in
'sheet(7)=A1_T_md
'sheet(8)=A1_T_ot

'sheet(9)=A2_T_in
'sheet(10)=A2_T_md
'sheet(11)=A2_T_ot

'sheet(12)=A3_T_in
'sheet(13)=A3_T_md
'sheet(14)=A3_T_ot

'sheet(15)=A4_T_in
'sheet(16)=A4_T_md
'sheet(17)=A4_T_ot

'sheet(18)=A1_P_in
'sheet(19)=A1_P_md
'sheet(20)=A1_P_ot

'sheet(21)=A2_P_in
'sheet(22)=A2_P_md
'sheet(23)=A2_P_ot

'sheet(24)=A3_P_in
'sheet(25)=A3_P_md
'sheet(26)=A3_P_ot

'sheet(27)=A4_P_in
'sheet(28)=A4_P_md
'sheet(29)=A4_P_ot




Dim i As Integer, j As Integer, k As Integer, l As Integer
Dim s1 As Integer, s2 As Integer, s3 As Integer, s4 As Integer
Dim slot As Integer
Dim p As Integer

'画面更新しない
Application.ScreenUpdating = False



slot = 30000

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A1_slot_no.
s1 = 2

For i = 10 To slot
    If (Cells(i, 2) <> 0) And (Cells(i - 1, 2) = 0) Then
        Worksheets(6).Cells(2, s1) = "slot" & Cells(i, 2)
        Worksheets(7).Cells(2, s1) = "slot" & Cells(i, 2)
        Worksheets(8).Cells(2, s1) = "slot" & Cells(i, 2)
        s1 = s1 + 1
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A1_h3po4_flow

k = 3

For i = 10 To slot
    If ((Cells(i, 2) = Cells(8, 2)) And (Cells(i + 1, 2) <> 0)) Then
        Worksheets(6).Cells(k, 34) = Cells(i, 7)
        Worksheets(7).Cells(k, 34) = Cells(i, 7)
        Worksheets(8).Cells(k, 34) = Cells(i, 7)
        k = k + 1
    ElseIf ((Cells(i, 2) = 0) And (Cells(i - 1, 2) = Cells(8, 2))) Then
        Exit For
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A1_temp_inside
'i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 2) = Worksheets(6).Cells(2, j) Then
        Worksheets(6).Cells(k, l) = Cells(i - 1, 13)
        k = k + 1
    ElseIf Cells(i, 2) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A1_temp_middle
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 2) = Worksheets(7).Cells(2, j) Then
        Worksheets(7).Cells(k, l) = Cells(i - 1, 14)
        k = k + 1
    ElseIf Cells(i, 2) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A1_temp_outside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 2) = Worksheets(8).Cells(2, j) Then
        Worksheets(8).Cells(k, l) = Cells(i - 1, 15)
        k = k + 1
    ElseIf Cells(i, 2) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A2_slot_no.
s2 = 2

For i = 10 To slot
    If (Cells(i, 22) <> 0) And (Cells(i - 1, 22) = 0) Then
        Worksheets(9).Cells(2, s2) = "slot" & Cells(i, 22)
        Worksheets(10).Cells(2, s2) = "slot" & Cells(i, 22)
        Worksheets(11).Cells(2, s2) = "slot" & Cells(i, 22)
        s2 = s2 + 1
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A2_h3po4_flow

k = 3

For i = 10 To slot
    If ((Cells(i, 22) = Cells(8, 22)) And (Cells(i + 1, 22) <> 0)) Then
        Worksheets(9).Cells(k, 34) = Cells(i, 27)
        Worksheets(10).Cells(k, 34) = Cells(i, 27)
        Worksheets(11).Cells(k, 34) = Cells(i, 27)
        k = k + 1
    ElseIf ((Cells(i, 22) = 0) And (Cells(i - 1, 22) = Cells(8, 22))) Then
        Exit For
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A2_temp_inside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 22) = Worksheets(9).Cells(2, j) Then
        Worksheets(9).Cells(k, l) = Cells(i - 1, 33)
        k = k + 1
    ElseIf Cells(i, 22) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A2_temp_middle
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 22) = Worksheets(10).Cells(2, j) Then
        Worksheets(10).Cells(k, l) = Cells(i - 1, 34)
        k = k + 1
    ElseIf Cells(i, 22) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A2_temp_outside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 22) = Worksheets(11).Cells(2, j) Then
        Worksheets(11).Cells(k, l) = Cells(i - 1, 35)
        k = k + 1
    ElseIf Cells(i, 22) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A3_slot_no.
s3 = 2

For i = 10 To slot
    If (Cells(i, 42) <> 0) And (Cells(i - 1, 42) = 0) Then
        Worksheets(12).Cells(2, s3) = "slot" & Cells(i, 42)
        Worksheets(13).Cells(2, s3) = "slot" & Cells(i, 42)
        Worksheets(14).Cells(2, s3) = "slot" & Cells(i, 42)
        s3 = s3 + 1
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A3_h3po4_flow

k = 3

For i = 10 To slot
    If ((Cells(i, 42) = Cells(8, 42)) And (Cells(i + 1, 42) <> 0)) Then
        Worksheets(12).Cells(k, 34) = Cells(i, 47)
        Worksheets(13).Cells(k, 34) = Cells(i, 47)
        Worksheets(14).Cells(k, 34) = Cells(i, 47)
        k = k + 1
    ElseIf ((Cells(i, 42) = 0) And (Cells(i - 1, 42) = Cells(8, 42))) Then
        Exit For
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A3_temp_inside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 42) = Worksheets(12).Cells(2, j) Then
        Worksheets(12).Cells(k, l) = Cells(i - 1, 53)
        k = k + 1
    ElseIf Cells(i, 42) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A3_temp_middle
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 42) = Worksheets(13).Cells(2, j) Then
        Worksheets(13).Cells(k, l) = Cells(i - 1, 54)
        k = k + 1
    ElseIf Cells(i, 42) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A3_temp_outside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 42) = Worksheets(14).Cells(2, j) Then
        Worksheets(14).Cells(k, l) = Cells(i - 1, 55)
        k = k + 1
    ElseIf Cells(i, 42) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A4_slot_no.
s4 = 2

For i = 10 To slot
    If (Cells(i, 62) <> 0) And (Cells(i - 1, 62) = 0) Then
        Worksheets(15).Cells(2, s4) = "slot" & Cells(i, 62)
        Worksheets(16).Cells(2, s4) = "slot" & Cells(i, 62)
        Worksheets(17).Cells(2, s4) = "slot" & Cells(i, 62)
        s4 = s4 + 1
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A4_h3po4_flow

k = 3

For i = 10 To slot
    If ((Cells(i, 62) = Cells(8, 62)) And (Cells(i + 1, 62) <> 0)) Then
        Worksheets(15).Cells(k, 34) = Cells(i, 67)
        Worksheets(16).Cells(k, 34) = Cells(i, 67)
        Worksheets(17).Cells(k, 34) = Cells(i, 67)
        k = k + 1
    ElseIf ((Cells(i, 62) = 0) And (Cells(i - 1, 62) = Cells(8, 62))) Then
        Exit For
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A4_temp_inside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 62) = Worksheets(15).Cells(2, j) Then
        Worksheets(15).Cells(k, l) = Cells(i - 1, 73)
        k = k + 1
    ElseIf Cells(i, 62) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A4_temp_middle
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 62) = Worksheets(16).Cells(2, j) Then
        Worksheets(16).Cells(k, l) = Cells(i - 1, 74)
        k = k + 1
    ElseIf Cells(i, 62) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i

'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
'A4_temp_outside
i = 10

j = 2
k = 3
l = 2

For i = 10 To slot
    If "slot" & Cells(i, 62) = Worksheets(17).Cells(2, j) Then
        Worksheets(17).Cells(k, l) = Cells(i - 1, 75)
        k = k + 1
    ElseIf Cells(i, 62) = 0 Then
        
    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i


'*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*

'画面更新する
Application.ScreenUpdating = True
End Sub
        """,
        "replace_settings_list":[
            {
            "target": """
s1 = slot_value

For i = 10 To slot_number
    If (Cells(i, col) <> 0) And (Cells(i - 1, col) = 0) Then
        Worksheets(ws1).Cells(2, s1) = "slot" & Cells(i, col)
        Worksheets(ws2).Cells(2, s1) = "slot" & Cells(i, col)
        Worksheets(ws3).Cells(2, s1) = "slot" & Cells(i, col)
        s1 = s1 + 1
    End If
Next i
""" ,

            "source_priority_word_list": ["col","ws1", "ws2", "ws3","slot_value","slot_number"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessSlotNumbers(col , slot_value , ws1 , ws2 , ws3 , slot_number )"
            },
             {
            "target": """
s2 = slot_value

For i = 10 To slot_number
    If (Cells(i, col) <> 0) And (Cells(i - 1, col) = 0) Then
        Worksheets(ws1).Cells(2, s2) = "slot" & Cells(i, col)
        Worksheets(ws2).Cells(2, s2) = "slot" & Cells(i, col)
        Worksheets(ws3).Cells(2, s2) = "slot" & Cells(i, col)
        s2 = s2 + 1
    End If
Next i
""" ,

            "source_priority_word_list": ["col","ws1", "ws2", "ws3","slot_value","slot_number"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessSlotNumbers(col , slot_value , ws1 , ws2 , ws3 , slot_number )"
            },
              {
            "target": """
s3 = slot_value

For i = 10 To slot_number
    If (Cells(i, col) <> 0) And (Cells(i - 1, col) = 0) Then
        Worksheets(ws1).Cells(2, s3) = "slot" & Cells(i, col)
        Worksheets(ws2).Cells(2, s3) = "slot" & Cells(i, col)
        Worksheets(ws3).Cells(2, s3) = "slot" & Cells(i, col)
        s3 = s3 + 1
    End If
Next i
""" ,

            "source_priority_word_list": ["col","ws1", "ws2", "ws3","slot_value","slot_number"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessSlotNumbers(col , slot_value , ws1 , ws2 , ws3 , slot_number )"
            },
               {
            "target": """
s4 = slot_value

For i = 10 To slot_number
    If (Cells(i, col) <> 0) And (Cells(i - 1, col) = 0) Then
        Worksheets(ws1).Cells(2, s4) = "slot" & Cells(i, col)
        Worksheets(ws2).Cells(2, s4) = "slot" & Cells(i, col)
        Worksheets(ws3).Cells(2, s4) = "slot" & Cells(i, col)
        s4 = s4 + 1
    End If
Next i
""" ,

            "source_priority_word_list": ["col","ws1", "ws2", "ws3","slot_value","slot_number"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessSlotNumbers(col , slot_value , ws1 , ws2 , ws3 , slot_number )"
            },
            {
            "target": """
j = col_j
k = row_k
l = col_l

For i = 10 To slot_number
    If "slot" & Cells(i, col) = Worksheets(wsIndex).Cells(2, j) Then
        Worksheets(wsIndex).Cells(k, l) = Cells(i - 1, tempCol)
        k = k + 1
    ElseIf Cells(i, col) = 0 Then

    Else
        j = j + 1
        l = l + 1
        k = 3
    End If
Next i
""" ,

            "source_priority_word_list": ["col","tempCol" , "wsIndex" , "slot_number","col_j","row_k","col_l"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessTemperature(col , tempCol , wsIndex , slot_number ,col_j,row_k,col_l)"
            },
            {"target": """
k = row_k

For i = 10 To slot
    If ((Cells(i, col) = Cells(8, col)) And (Cells(i + 1, col) <> 0)) Then
        Worksheets(ws1).Cells(k, 34) = Cells(i, dataCol)
        Worksheets(ws2).Cells(k, 34) = Cells(i, dataCol)
        Worksheets(ws3).Cells(k, 34) = Cells(i, dataCol)
        k = k + 1
    ElseIf ((Cells(i, col) = 0) And (Cells(i - 1, col) = Cells(8, col))) Then
        Exit For
    End If
Next i
""" ,

            "source_priority_word_list": ["ws1","ws2","ws3","col","dataCol" , "wsIndex" , "slot_number","col_j","row_k","col_l"],
            "ignore_word_list": [" ", "\t","\n"],
            "sign_list": ["(",")","=",","],
            "replace_word": "Call ProcessFlow(col , dataCol , ws1 , ws2 , ws3 , slot_number,row_k)"
            }
      
        ]
    }
    source_code =TextControl.replace_function_call(default_settings)    
    print (source_code)
    """
    ProcessSlotNumbers(col As Integer, ByRef slot_value As Integer, ws1 As Integer, ws2 As Integer, ws3 As Integer, slot As Integer)
        Dim i As Integer
        s1=slot_value
        For i = 10 To slot
            If (Cells(i, col) <> 0) And (Cells(i - 1, col) = 0) Then
                Worksheets(ws1).Cells(2, s1) = "slot" & Cells(i, col)
                Worksheets(ws2).Cells(2, s1) = "slot" & Cells(i, col)
                Worksheets(ws3).Cells(2, s1) = "slot" & Cells(i, col)
                s1 = s1 + 1
            End If
        Next i
    End Sub
    
    Sub ProcessTemperature(col As Integer, tempCol As Integer, wsIndex As Integer, slot As Integer)
        Dim i As Integer, j As Integer, k As Integer, l As Integer
        j = 2: 
        k = 3: 
        l = 2
        For i = 10 To slot
            If "slot" & Cells(i, col) = Worksheets(wsIndex).Cells(2, j) Then
                Worksheets(wsIndex).Cells(k, l) = Cells(i - 1, tempCol)
                k = k + 1
            ElseIf Cells(i, col) = 0 Then
            Else
                j = j + 1
                l = l + 1
                k = 3
            End If
        Next i
    End Sub
    Sub ProcessFlow(col As Integer, dataCol As Integer, ws1 As Integer, ws2 As Integer, ws3 As Integer, slot As Integer)
        Dim i As Integer, k As Integer
        k = 3
        For i = 10 To slot
            If (Cells(i, col) = Cells(8, col)) And (Cells(i + 1, col) <> 0) Then
                Worksheets(ws1).Cells(k, 34) = Cells(i, dataCol)
                Worksheets(ws2).Cells(k, 34) = Cells(i, dataCol)
                Worksheets(ws3).Cells(k, 34) = Cells(i, dataCol)
                k = k + 1
            ElseIf (Cells(i, col) = 0) And (Cells(i - 1, col) = Cells(8, col)) Then
                Exit For
            End If
        Next i
    End Sub
    """
if __name__ == '__main__':
    main()