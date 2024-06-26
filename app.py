from flask import Flask, render_template,request, send_file
import pandas as pd
import xlsxwriter
from io import BytesIO

classes = []
app = Flask(__name__)
TOTAL_HRS = 7
DAYS = 5
MAX_SIZE = 120
GAP = 17

wb = xlsxwriter.Workbook('Timetable.xlsx')
ws = wb.add_worksheet("TimeTable")
ws2 = wb.add_worksheet("TeacherSlot")
f2 = wb.add_format({'bold': True, 'bg_color': '#737373'})
f3 = wb.add_format({'bg_color': '#808080'})
f4 = wb.add_format({'bold': True, 'bg_color': '#808080'})
f5 = wb.add_format({'bg_color': '#737373'})
f6 = wb.add_format({'bold': True, 'bg_color': '#999999'})
working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def populate(s):
    length = len(s)
    list_1 = []
    class_ind = []
    for k in range(length):
        if str(s.iat[k,1]).lower() != 'nan':
            class_ind.append(list((s.iat[k,0], s.iat[k,1])))
        else:
            if class_ind:
                list_1.append(class_ind)
            classes.append(str(s.iat[k,0]))
            class_ind = []
    list_1.append(class_ind)
    return list_1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/page2.html')
def page2():
    return render_template('page2.html')

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_file('static/' +filename, as_attachment=True)

@app.route('/view', methods=['POST'])
def view():
    files = [request.files[f'file{i}'] for i in range(1, 4)]
    s2 = pd.read_excel(files[0])  # partially filled
    s1 = pd.read_excel(files[1])  # course teacher mapped
    s3 = pd.read_excel(files[2])  # course hour mapped file
    teachers = s1['faculty'].dropna().unique().tolist()

    teacher_course = populate(s1)
    teacher_len = len(teachers)

    t_len = len(s2)
    course_hour = populate(s3)
    timeslot = [[0] * MAX_SIZE for _ in range(t_len)]
    teacherslot = [[0] * MAX_SIZE for _ in range(teacher_len)]

    for i in range(t_len):
        index = 0
        for k in range(DAYS):
            for j in range(TOTAL_HRS):
                timeslot[i][index] = str(s2.iat[i,(k * TOTAL_HRS) + j])
                index += 1
            index += GAP

    for k in range(t_len):
        c_t = teacher_course[k]
        c_h = course_hour[k]
        for i in range(len(c_h)):
            course = c_h[i][0]
            hour = c_h[i][1]
            faculty = [inner_list[1] for inner_list in c_t if inner_list[0] == course]
            fac = faculty[0]
            t_index = teachers.index(fac)
            alloc_hr = 0
            rem_hr = hour
            slots = []
            while rem_hr > 0:
                for j in range(MAX_SIZE):
                    if str(timeslot[k][j]).lower() == "nan":
                        begin = j
                        break
                for j in range((MAX_SIZE - 1), -1, -1):
                    if str(timeslot[k][j]).lower() == "nan":
                        end = j
                        break
                if rem_hr != 1:
                    interval = (end - begin + 1) / (rem_hr - 1)
                pos = begin
                for j in range(int(rem_hr)):
                    slots.append(pos)
                    pos += interval
                for slot in slots:
                    if str(timeslot[k][int(slot)]).lower() == "nan" and teacherslot[t_index][int(slot)] == 0:
                        timeslot[k][int(slot)] = course
                        teacherslot[t_index][int(slot)] = course
                    else:
                        left = int(slot) - 1
                        right = int(slot) + 1
                        while left > 0 or right < MAX_SIZE:
                            if ((left > 0 and str(timeslot[k][left]).lower() == "nan")) and teacherslot[t_index][left] == 0:
                                timeslot[k][left] = course
                                teacherslot[t_index][left] = course
                                break
                            if (right < MAX_SIZE and str(timeslot[k][right]).lower() == "nan") and teacherslot[t_index][right] == 0:
                                timeslot[k][right] = course
                                teacherslot[t_index][right] = course
                                break
                            left = left - 1
                            right = right + 1
                        if left < 0 and right >= MAX_SIZE:
                            print("ERROR: ALLOCATION COULD NOT BE DONE")
                            break

                    rem_hr -= 1
                else:
                    continue
                break

    k = 0
    timetable = []
    counter = 0
    while k < t_len:
        index = 0
        temp = [[0] * TOTAL_HRS for _ in range(DAYS)]
        timetable.append(['', '', '', classes[k], '', '', ''])
        for i in range(DAYS):
            for j in range(TOTAL_HRS):
                if str(timeslot[k][index]).lower() == "nan":
                    timeslot[k][index] = "REMEDIAL"
                temp[i][j] = timeslot[k][index]
                index += 1
            timetable.append(temp[i])
            index += GAP
        ws2.write(counter, 4, teachers[k])
        if k % 2 == 0:
            ws2.write_row(counter + 1, 0, ['', '1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'], f2)
        else:
            ws2.write_row(counter + 1, 0, ['', '1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'], f4)
        for row in range(len(temp)):
            if k % 2 == 0:
                ws2.write(counter + row + 2, 0, working_days[row], f2)
            else:
                ws2.write(counter + row + 2, 0, working_days[row], f4)
            for col, value in enumerate(temp[row]):
                if k % 2 == 0:
                    ws2.write(counter + row + 2, col + 1, value)
                else:
                    ws2.write(counter + row + 2, col + 1, value, f3)
        counter += 8
        k += 1

    k = 0
    teachslot = []
    counter = 0
    while k < teacher_len:
        index = 0
        tech = [[0] * TOTAL_HRS for _ in range(DAYS)]
        teachslot.append([teachers[k], '', '', '', '', '', ''])
        for i in range(DAYS):
            for j in range(TOTAL_HRS):
                if teacherslot[k][index] == 0:
                    teacherslot[k][index] = "-"
                tech[i][j] = teacherslot[k][index]
                index += 1
            teachslot.append(tech[i])
            index += GAP
        ws2.write(counter, 4, teachers[k])
        if k % 2 == 0:
            ws2.write_row(counter + 1, 0, ['', '1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'], f2)
        else:
            ws2.write_row(counter + 1, 0, ['', '1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'], f4)
        for row in range(len(temp)):
            if k % 2 == 0:
                ws2.write(counter + row + 2, 0, working_days[row], f2)
            else:
                ws2.write(counter + row + 2, 0, working_days[row], f4)
            for col, value in enumerate(temp[row]):
                if k % 2 == 0:
                    ws2.write(counter + row + 2, col + 1, value)
                else:
                    ws2.write(counter + row + 2, col + 1, value, f3)
        counter += 8
        k = k + 1

    wb.close()

    # output = BytesIO()
    # #with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    #  #   tf = pd.DataFrame(timetable, index=['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] * t_len,columns=['1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'])
    #   #  tc = pd.DataFrame(teachslot,index=['FACULTY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'] * teacher_len,columns=['1st', '2nd', '3rd', 'Lunch', '4th', '5th', '6th'])
    #    # tf.to_excel(writer, sheet_name="Timetable")
    #     #tc.to_excel(writer, sheet_name="Teacher Slots")

    # output.seek(0)
    #return send_file(output,as_attachment=True,attachment_filename='Timetable.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return send_file("static/final.xlsx",as_attachment=True)
if __name__ == '__main__':
    app.run(debug=True)
