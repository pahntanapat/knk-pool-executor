# Test (โจทย์)

## อธิบาย


## ทำอะไรบ้าง

### 1. Fork Branch นี้ใน Github อันนี้ไปบน Git ตัวเอง
- ตั้งเป็น Public หรือ Private git ก็ได้  ถ้าตั้งเป็น Private git
- ให้ invite `pahntanapat` เข้าไปเป็น collaborator ด้วย


### 2. ทดสอบ+Debug Class 3 อันนี้ ให้ทำงานได้ (ดูตัวอย่างใน `test/simple_test.py`)  
```python
StackTracedThreadPoolExecutor
StackTracedProcessPoolExecutor
PipeProcessPoolExecutor
```
  
1. ทำงานปกติเหมือน `ThreadPoolExecutor` หรือ `ProcessPoolExecutor` มาตรฐาน
2. เมื่อเกิด Exception ให้มี original stack trace ติดมาด้วย

### 3. เขียน `test/test.py` เพื่อทดสอบว่าทำงาน parallel ได้ไหม  
**Definition**: Parallel computing = ประมวลผลพร้อมกันได้ = เวลาทำงานลดลง  
**ดังนั้น!**: ต้องจับเวลาทำงานของ script

### Test Scenario
1. `sleep()`
2. GIL-released process: คิดให้แล้วว่าใช้ `numpy` <br>ซึ่งทำงาน multi-cpu parallel ด้วยตัวมันเอง
   ```python
np.log(np.arange(1,100000000))
   ```
3. GIL process: python function ทั่วๆ ไป  คิดว่าน่าจะใช้ <br>
   ```python
tuple(log(i) for i in range(1,100000000))
```
  
**ทั้ง 3 Scenarios ต้องทำ**
1. ทำครั้งเดียว
2. ทำซ้ำเท่าจำนวน CPU core
3. ทำซ้ำเท่าจำนวน 2 เท่าของ CPU core 
4. ทำซ้ำเท่าจำนวน 4 เท่าของ CPU core
  
**และต้องทำเปรียบเทียบระหว่าง 4 แบบ**  
1. serial processing (for loop ธรรมดา)
2. StackTracedThreadPoolExecutor
3. StackTracedProcessPoolExecutor
4. PipeProcessPoolExecutor

**สรุป**มี 48 scenarios

### 4. เตรียมไฟล์อื่นๆ แล้ว Push ขึ้น [test.pypi.org]  
- ใส่ชื่อตัวเองเป็น co-authors
- ห้ามเอาขึ้น Production Package index
