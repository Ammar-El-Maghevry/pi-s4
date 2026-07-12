import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  createStudent,
  deleteStudent,
  fetchStudentPhotoUrl,
  importStudents,
  listStudents,
  uploadStudentPhoto,
} from "../api/students";
import {
  createTeacher,
  deleteTeacher,
  fetchTeacherPhotoUrl,
  getTeacherAttendance,
  listTeachers,
  setTeacherPresent,
  uploadTeacherPhoto,
} from "../api/teachers";
import { Modal } from "../components/Modal";
import { PhotoCaptureModal } from "../components/PhotoCaptureModal";
import { PhotoPicker } from "../components/PhotoPicker";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { todayIso } from "../lib/time";
import type { Student, StudentImportResult, Teacher } from "../lib/types";

type Tab = "students" | "teachers";

export function PeoplePage() {
  const { showError, showSuccess } = useToast();
  const [tab, setTab] = useState<Tab>("students");
  const [search, setSearch] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherAttendance, setTeacherAttendance] = useState<Record<number, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [photoTarget, setPhotoTarget] = useState<Student | null>(null);
  const [teacherPhotoTarget, setTeacherPhotoTarget] = useState<Teacher | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);

  async function load() {
    setIsLoading(true);
    try {
      if (tab === "students") {
        setStudents(await listStudents(search));
      } else {
        const [teacherData, attendance] = await Promise.all([
          listTeachers(search),
          getTeacherAttendance(todayIso()),
        ]);
        setTeachers(teacherData);
        setTeacherAttendance(attendance);
      }
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  useEffect(() => {
    const id = setTimeout(load, 250);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  async function handleDeleteStudent(id: number) {
    if (!confirm("Remove this student?")) return;
    try {
      await deleteStudent(id);
      showSuccess("Student removed");
      load();
    } catch (err) {
      showError(apiErrorMessage(err));
    }
  }

  async function handleDeleteTeacher(id: number) {
    if (!confirm("Remove this teacher?")) return;
    await deleteTeacher(id);
    showSuccess("Teacher removed");
    load();
  }

  async function handleToggleTeacherPresent(id: number) {
    const next = !teacherAttendance[id];
    setTeacherAttendance((prev) => ({ ...prev, [id]: next }));
    await setTeacherPresent(id, todayIso(), next);
  }

  async function handlePhotoCapture(photo: Blob) {
    if (!photoTarget) return;
    setPhotoError(null);
    setIsUploadingPhoto(true);
    try {
      await uploadStudentPhoto(photoTarget.id, photo);
      showSuccess("Photo enrolled — face embedding computed");
      setPhotoTarget(null);
      load();
    } catch (err) {
      setPhotoError(apiErrorMessage(err));
    } finally {
      setIsUploadingPhoto(false);
    }
  }

  function openPhotoTargetFor(id: number, fullName: string, studentId: string) {
    setPhotoError(null);
    setPhotoTarget({
      id,
      full_name: fullName,
      student_id: studentId,
      email: null,
      department: null,
      class_name: null,
      photo_path: null,
      has_face_embedding: false,
      created_at: "",
      updated_at: "",
    });
  }

  async function handleTeacherPhotoCapture(photo: Blob) {
    if (!teacherPhotoTarget) return;
    setPhotoError(null);
    setIsUploadingPhoto(true);
    try {
      await uploadTeacherPhoto(teacherPhotoTarget.id, photo);
      showSuccess("Photo enrolled — face embedding computed");
      setTeacherPhotoTarget(null);
      load();
    } catch (err) {
      setPhotoError(apiErrorMessage(err));
    } finally {
      setIsUploadingPhoto(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">People</h1>
          <p className="text-sm text-text-muted">Manage enrolled students and teachers</p>
        </div>
        <div className="flex items-center gap-2">
          {tab === "students" && (
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-bg-inset"
            >
              Import
            </button>
          )}
          <button
            onClick={() => setIsModalOpen(true)}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
          >
            + Add {tab === "students" ? "student" : "teacher"}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-1 rounded-lg border border-border bg-bg-elevated p-1">
          {(["students", "teachers"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                tab === t ? "bg-accent-soft text-accent" : "text-text-muted hover:text-text"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, ID, or department…"
          className="w-72 rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
        />
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        {tab === "students" ? (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
                <th className="px-5 py-3 font-medium">Photo</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Student ID</th>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Department</th>
                <th className="px-5 py-3 font-medium">Class</th>
                <th className="px-5 py-3 font-medium">Live status</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <TableLoading colSpan={8} />
              ) : students.length === 0 ? (
                <TableEmpty colSpan={8} />
              ) : (
                students.map((s) => (
                  <tr key={s.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3">
                      <button
                        onClick={() => {
                          setPhotoError(null);
                          setPhotoTarget(s);
                        }}
                        title={s.has_face_embedding ? "Retake photo" : "Add photo"}
                      >
                        <StudentAvatar student={s} />
                      </button>
                    </td>
                    <td className="px-5 py-3 font-medium">{s.full_name}</td>
                    <td className="px-5 py-3 font-data text-text-muted">{s.student_id}</td>
                    <td className="px-5 py-3 text-text-muted">{s.email ?? "—"}</td>
                    <td className="px-5 py-3 text-text-muted">{s.department ?? "—"}</td>
                    <td className="px-5 py-3 text-text-muted">{s.class_name ?? "—"}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          s.has_face_embedding
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-border bg-bg-inset text-text-muted"
                        }`}
                      >
                        {s.has_face_embedding ? "Enrolled" : "Not enrolled"}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleDeleteStudent(s.id)}
                        className="text-xs text-text-muted hover:text-absent"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
                <th className="px-5 py-3 font-medium">Photo</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Live status</th>
                <th className="px-5 py-3 font-medium">Today</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <TableLoading colSpan={6} />
              ) : teachers.length === 0 ? (
                <TableEmpty colSpan={6} />
              ) : (
                teachers.map((t) => (
                  <tr key={t.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3">
                      <button
                        onClick={() => {
                          setPhotoError(null);
                          setTeacherPhotoTarget(t);
                        }}
                        title={t.has_face_embedding ? "Retake photo" : "Add photo"}
                      >
                        <TeacherAvatar teacher={t} />
                      </button>
                    </td>
                    <td className="px-5 py-3 font-medium">{t.full_name}</td>
                    <td className="px-5 py-3 text-text-muted">{t.email ?? "—"}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          t.has_face_embedding
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-border bg-bg-inset text-text-muted"
                        }`}
                      >
                        {t.has_face_embedding ? "Enrolled" : "Not enrolled"}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => handleToggleTeacherPresent(t.id)}
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          teacherAttendance[t.id]
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-border bg-bg-inset text-text-muted"
                        }`}
                      >
                        {teacherAttendance[t.id] ? "Present" : "Absent"}
                      </button>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleDeleteTeacher(t.id)}
                        className="text-xs text-text-muted hover:text-absent"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
        {tab === "teachers" && (
          <p className="border-t border-border px-5 py-2 text-xs text-text-muted">
            Enroll a photo (click a teacher's avatar) so the live camera can recognize them and mark
            them present automatically — same as students. "Today" also lets you mark it by hand.
          </p>
        )}
      </div>

      {isModalOpen && (
        <AddPersonModal
          tab={tab}
          onClose={() => setIsModalOpen(false)}
          onCreated={() => {
            setIsModalOpen(false);
            load();
          }}
        />
      )}

      {photoTarget && (
        <PhotoCaptureModal
          title={`Enroll photo — ${photoTarget.full_name}`}
          onClose={() => setPhotoTarget(null)}
          onCapture={handlePhotoCapture}
          isSubmitting={isUploadingPhoto}
          error={photoError}
        />
      )}

      {teacherPhotoTarget && (
        <PhotoCaptureModal
          title={`Enroll photo — ${teacherPhotoTarget.full_name}`}
          onClose={() => setTeacherPhotoTarget(null)}
          onCapture={handleTeacherPhotoCapture}
          isSubmitting={isUploadingPhoto}
          error={photoError}
        />
      )}
    </div>
  );
}

function StudentAvatar({ student }: { student: Student }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!student.has_face_embedding) {
      setUrl(null);
      return;
    }
    let objectUrl: string | null = null;
    fetchStudentPhotoUrl(student.id).then((u) => {
      objectUrl = u;
      setUrl(u);
    });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [student.id, student.has_face_embedding]);

  if (url) {
    return <img src={url} alt={student.full_name} className="h-9 w-9 rounded-full object-cover" />;
  }
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-full border border-dashed border-border text-text-muted">
      <span className="text-xs">+</span>
    </div>
  );
}

function TeacherAvatar({ teacher }: { teacher: Teacher }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!teacher.has_face_embedding) {
      setUrl(null);
      return;
    }
    let objectUrl: string | null = null;
    fetchTeacherPhotoUrl(teacher.id).then((u) => {
      objectUrl = u;
      setUrl(u);
    });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [teacher.id, teacher.has_face_embedding]);

  if (url) {
    return <img src={url} alt={teacher.full_name} className="h-9 w-9 rounded-full object-cover" />;
  }
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-full border border-dashed border-border text-text-muted">
      <span className="text-xs">+</span>
    </div>
  );
}

function AddPersonModal({
  tab,
  onClose,
  onCreated,
}: {
  tab: Tab;
  onClose: () => void;
  onCreated: () => void;
}) {
  const { showError, showSuccess } = useToast();
  const [fullName, setFullName] = useState("");
  const [idNumber, setIdNumber] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("");
  const [photo, setPhoto] = useState<Blob | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (tab === "students") {
        const student = await createStudent({
          full_name: fullName,
          student_id: idNumber,
          email: email || null,
          department: department || null,
        });
        if (photo) {
          try {
            await uploadStudentPhoto(student.id, photo);
            showSuccess("Student added with photo enrolled");
          } catch (photoErr) {
            showError(`Student added, but photo upload failed: ${apiErrorMessage(photoErr)}`);
          }
        } else {
          showSuccess("Student added");
        }
      } else {
        const teacher = await createTeacher({ full_name: fullName, email: email || null });
        if (photo) {
          try {
            await uploadTeacherPhoto(teacher.id, photo);
            showSuccess("Teacher added with photo enrolled");
          } catch (photoErr) {
            showError(`Teacher added, but photo upload failed: ${apiErrorMessage(photoErr)}`);
          }
        } else {
          showSuccess("Teacher added");
        }
      }
      onCreated();
    } catch (err) {
      showError(err instanceof Error && !("isAxiosError" in err) ? err.message : apiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={`Add ${tab === "students" ? "student" : "teacher"}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <Field label="Full name" value={fullName} onChange={setFullName} required />
        {tab === "students" && (
          <>
            <Field label="Student ID" value={idNumber} onChange={setIdNumber} required />
            <Field label="Department" value={department} onChange={setDepartment} />
          </>
        )}
        <Field label="Email" value={email} onChange={setEmail} type="email" />
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
            Photo (optional — enroll now so the live camera can recognize them)
          </label>
          <PhotoPicker value={photo} onChange={setPhoto} height={200} />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
        >
          {isSubmitting ? "Saving…" : "Save"}
        </button>
      </form>
    </Modal>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
        {label}
      </label>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
      />
    </div>
  );
}
