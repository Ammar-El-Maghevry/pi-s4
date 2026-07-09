# وصف مخطط الفئات (Diagramme de Classes) - قاعدة البيانات

## نظرة عامة

قاعدة البيانات تتكون من **7 جداول** تعمل معًا لتسجيل حضور الطلاب باستخدام التعرف على الوجه. الجداول مقسمة إلى 3 مجموعات:

---

## 1. جدول المستخدمين (Users) - المصادقة

```sql
TABLE users
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| email | str (UNIQUE) | البريد الإلكتروني للمشرف |
| full_name | str | الاسم الكامل |
| hashed_password | str | كلمة المرور مشفرة (bcrypt) |
| is_active | bool | هل الحساب نشط |
| created_at | datetime | تاريخ الإنشاء |

**الغرض**: تخزين حسابات المشرفين (Administrateurs) الذين يدخلون إلى النظام.
**ملاحظة**: هذا الجدول **مستقل** ولا يرتبط بأي جدول آخر لأنه خاص بالمصادقة فقط.

---

## 2. جدول الطلاب (Students) - البيانات الأساسية

```sql
TABLE students
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| full_name | str (INDEX) | الاسم الكامل |
| student_id | str (UNIQUE, INDEX) | الرقم الجامعي |
| email | str? | البريد الإلكتروني (اختياري) |
| department | str? | القسم (اختياري) |
| photo_path | str? | مسار الصورة على القرص |
| face_embedding | Vector(512)? | البصمة الوجهية (متجه 512 رقم) |
| created_at | datetime | تاريخ الإنشاء |
| updated_at | datetime | تاريخ التحديث |

**الغرض**: تخزين معلومات الطلاب الأساسية وبصماتهم الوجهية للتعرف عليهم لاحقًا.

**العلاقات**:
- يرتبط بجدول `AttendanceEvent` (1 → *) : طالب واحد يولد عدة أحداث دخول/خروج
- يرتبط بجدول `AttendanceResult` (1 → *) : طالب واحد له عدة نتائج حضور
- يرتبط بجدول `Snapshot` (1 → *) : طالب واحد له عدة صور ملتقطة

---

## 3. جدول المواعيد (Schedules) - الجدول الزمني

```sql
TABLE schedules
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| session_number | int | رقم الحصة (1, 2, 3...) |
| name | str | اسم الحصة |
| start_time | Time | وقت البداية |
| end_time | Time | وقت النهاية |
| session_type | SessionType | نوع الحصة (حصة / استراحة) |
| camera_id | int? (FK → cameras) | الكاميرا المخصصة لهذه الحصة |

**الغرض**: تحديد أوقات الحصص الدراسية في اليوم. يتم ملؤها تلقائيًا عند بدء التشغيل (5 حصص + 4 استراحات) ويمكن تعديلها عبر API.

**العلاقات**:
- يرتبط بجدول `AttendanceResult` (1 → *) : حصة واحدة لها عدة نتائج حضور
- يرتبط بجدول `Camera` (* → 0..1) : عدة حصص يمكن ربطها بكاميرا واحدة أو عدم ربطها

---

## 4. جدول الكاميرات (Cameras)

```sql
TABLE cameras
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| name | str | اسم الكاميرا (مثلاً "القاعة أ") |
| location | str? | الموقع (اختياري) |
| source_type | CameraSourceType | نوع المصدر (كاميرا IP / هاتف) |
| source_url | str | رابط المصدر (للـ IP) أو placeholder (للهاتف) |
| webrtc_token | str? (UNIQUE) | رمز الاقتران للهاتف |
| pairing_email | str? | البريد الإلكتروني لإرسال رابط الاقتران |
| is_active | bool | هل الكاميرا نشطة |
| line_x1..y2 | int? | إحداثيات خط العبور الافتراضي |
| crossing_direction | CrossingDirection | اتجاه العبور (فوق→تحت = دخول) |
| min_crossing_frames | int | الحد الأدنى من الإطارات لتأكيد العبور |
| cooldown_seconds | int | فترة التهدئة بين الأحداث (بالثواني) |
| present_threshold | float | عتبة الحضور (مثلاً 0.7 = 70%) |
| late_threshold | float | عتبة التأخير (مثلاً 0.2 = 20%) |
| face_match_threshold | float | عتبة تطابق الوجه |
| created_at | datetime | تاريخ الإنشاء |
| updated_at | datetime | تاريخ التحديث |

**الغرض**: تخزين إعدادات كل كاميرا مثبتة في القاعات. تدعم نوعين: كاميرات IP تقليدية أو كاميرات الهواتف عبر WebRTC.

**العلاقات**:
- يرتبط بجدول `Schedule` (1 → *) : كاميرا واحدة يمكن ربطها بعدة حصص

---

## 5. جدول أحداث الحضور (AttendanceEvents)

```sql
TABLE attendance_events
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| student_id | int (FK → students) | الطالب المرتبط |
| event_type | EventType | نوع الحدث (دخول / خروج) |
| timestamp | datetime (INDEX) | وقت الحدث |
| confidence | float? | درجة الثقة في التعرف (اختياري) |
| camera_id | str? | معرف الكاميرا كنص (اختياري) |
| snapshot_id | int? (FK → snapshots) | اللقطة المرتبطة (اختياري) |

**الغرض**: تسجيل كل حدث دخول أو خروج للطلاب. هذه هي البيانات الخام التي يتم جمعها من الكاميرات أو إدخالها يدويًا.

**العلاقات**:
- يرتبط بجدول `Student` (* → 1) : كل حدث ينتمي لطالب واحد
- يرتبط بجدول `Snapshot` (* → 0..1) : كل حدث قد يكون مرتبطًا بصورة أو لا

---

## 6. جدول نتائج الحضور (AttendanceResults)

```sql
TABLE attendance_results
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| student_id | int (FK → students) | الطالب |
| schedule_id | int (FK → schedules) | الحصة |
| result_date | date (INDEX) | التاريخ |
| status | AttendanceStatus | الحالة (حاضر / متأخر / غائب) |
| entry_time | datetime? | وقت الدخول الفعلي |
| exit_time | datetime? | وقت الخروج الفعلي |
| computed_at | datetime | وقت حساب النتيجة |

**قيود**: `UNIQUE(student_id, schedule_id, result_date)` - لا يمكن تكرار نفس النتيجة لنفس الطالب في نفس الحصة في نفس اليوم.

**الغرض**: تخزين نتائج الحضور المحسوبة لكل طالب في كل حصة. يتم حسابها بناءً على أحداث الدخول/الخروج.

**العلاقات**:
- يرتبط بجدول `Student` (* → 1) : كل نتيجة تنتمي لطالب واحد
- يرتبط بجدول `Schedule` (* → 1) : كل نتيجة تنتمي لحصة واحدة

---

## 7. جدول اللقطات (Snapshots)

```sql
TABLE snapshots
```

| الحقل | النوع | الشرح |
|-------|------|-------|
| id | int (PK) | المعرف الفريد |
| student_id | int? (FK → students) | الطالب (اختياري، قد يكون مجهولًا) |
| image_path | str | مسار الصورة على القرص |
| event_type | EventType | نوع الحدث عند التقاط الصورة |
| captured_at | datetime | وقت الالتقاط |

**الغرض**: تخزين صور ملتقطة من الكاميرا عند حدوث حدث دخول أو خروج. حاليًا الجدول موجود لكنه لا يُملأ تلقائيًا بعد.

**العلاقات**:
- يرتبط بجدول `Student` (* → 1) : كل لقطة قد تنتمي لطالب أو لا
- يرتبط بجدول `AttendanceEvent` (0..1 → *) : كل لقطة قد ترتبط بعدة أحداث أو لا

---

## ملخص العلاقات

```
User        → (لا توجد علاقات) - جدول مستقل للمصادقة
Student     1 → * AttendanceEvent
Student     1 → * AttendanceResult
Student     1 → * Snapshot
Schedule    1 → * AttendanceResult
Schedule    * → 0..1 Camera
Camera      1 → * Schedule
AttendanceEvent * → 0..1 Snapshot
```

## أنواع البيانات المخصصة (Énumérations)

| النوع | القيم |
|-------|-------|
| EventType | `entry` (دخول), `exit` (خروج) |
| SessionType | `session` (حصة), `break` (استراحة) |
| AttendanceStatus | `present` (حاضر), `late` (متأخر), `absent` (غائب) |
| CrossingDirection | `top_to_bottom_is_entry` (فوق→تحت = دخول), `bottom_to_top_is_entry` (تحت→فوق = دخول) |
| CameraSourceType | `ip_camera` (كاميرا IP), `phone` (هاتف) |
