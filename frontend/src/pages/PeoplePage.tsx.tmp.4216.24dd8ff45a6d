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
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { todayIso } from "../lib/time";
import type { Student, StudentImportResult, Teacher } from "../lib/types";

type Tab = "students" | "teachers";

export function PeoplePage() {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
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
    if (!confirm(t.people.confirmRemoveStudent)) return;
    try {
      await deleteStudent(id);
      showSuccess(t.people.toastStudentRemoved);
      load();
    } catch (err) {
      showError(apiErrorMessage(err));
    }
  }

  async function handleDeleteTeacher(id: number) {
    if (!confirm(t.people.confirmRemoveTeacher)) return;
    await deleteTeacher(id);
    showSuccess(t.people.toastTeacherRemoved);
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
      showSuccess(t.people.toastPhotoEnrolled);
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
      showSuccess(t.people.toastPhotoEnrolled);
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
          <h1 className="text-2xl font-semibold">{t.people.title}</h1>
          <p className="text-sm text-text-muted">{t.people.subtitle}</p>
        </div>
        <div className="flex items-center gap-2">
          {tab === "students" && (
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-bg-inset"
            >
              {t.common.import}
            </button>
          )}
          <button
            onClick={() => setIsModalOpen(true)}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
          >
            {tab === "students" ? t.people.addStudent : t.people.addTeacher}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-1 rounded-lg border border-border bg-bg-elevated p-1">
          {(["students", "teachers"] as Tab[]).map((tabKey) => (
            <button
              key={tabKey}
              onClick={() => setTab(tabKey)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === tabKey ? "bg-accent-soft text-accent" : "text-text-muted hover:text-text"
              }`}
            >
              {tabKey === "students" ? t.people.tabStudents : t.people.tabTeachers}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t.people.searchPlaceholder}
          className="w-72 rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
        />
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        {tab === "students" ? (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
                <th className="px-5 py-3 font-medium">{t.people.colPhoto}</th>
                <th className="px-5 py-3 font-medium">{t.people.colName}</th>
                <th className="px-5 py-3 font-medium">{t.people.colStudentId}</th>
                <th className="px-5 py-3 font-medium">{t.people.colEmail}</th>
                <th className="px-5 py-3 font-medium">{t.people.colDepartment}</th>
                <th className="px-5 py-3 font-medium">{t.people.colClass}</th>
                <th className="px-5 py-3 font-medium">{t.people.colLiveStatus}</th>
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
                        title={s.has_face_embedding ? t.people.retakePhotoTitle : t.people.addPhotoTitle}
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
                        {s.has_face_embedding ? t.people.enrolled : t.people.notEnrolled}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleDeleteStudent(s.id)}
                        className="text-xs text-text-muted hover:text-absent"
                      >
                        {t.common.remove}
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
                <th className="px-5 py-3 font-medium">{t.people.colPhoto}</th>
                <th className="px-5 py-3 font-medium">{t.people.colName}</th>
                <th className="px-5 py-3 font-medium">{t.people.colEmail}</th>
                <th className="px-5 py-3 font-medium">{t.people.colLiveStatus}</th>
                <th className="px-5 py-3 font-medium">{t.people.colToday}</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <TableLoading colSpan={6} />
              ) : teachers.length === 0 ? (
                <TableEmpty colSpan={6} />
              ) : (
                teachers.map((teacher) => (
                  <tr key={teacher.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3">
                      <button
                        onClick={() => {
                          setPhotoError(null);
                          setTeacherPhotoTarget(teacher);
                        }}
                        title={teacher.has_face_embedding ? t.people.retakePhotoTitle : t.people.addPhotoTitle}
                      >
                        <TeacherAvatar teacher={teacher} />
                      </button>
                    </td>
                    <td className="px-5 py-3 font-medium">{teacher.full_name}</td>
                    <td className="px-5 py-3 text-text-muted">{teacher.email ?? "—"}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          teacher.has_face_embedding
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-border bg-bg-inset text-text-muted"
                        }`}
                      >
                        {teacher.has_face_embedding ? t.people.enrolled : t.people.notEnrolled}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => handleToggleTeacherPresent(teacher.id)}
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          teacherAttendance[teacher.id]
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-border bg-bg-inset text-text-muted"
                        }`}
                      >
                        {teacherAttendance[teacher.id] ? t.statusPill.present : t.statusPill.absent}
                      </button>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleDeleteTeacher(teacher.id)}
                        className="text-xs text-text-muted hover:text-absent"
                      >
                        {t.common.remove}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
        {tab === "teachers" && (
          <p className="border-t border-border px-5 py-2 text-xs text-text-muted">{t.people.teachersHint}</p>
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

      {isImportModalOpen && (
        <ImportStudentsModal
          onClose={() => setIsImportModalOpen(false)}
          onImported={() => load()}
          onAddPhoto={(id, fullName, studentId) => {
            setIsImportModalOpen(false);
            openPhotoTargetFor(id, fullName, studentId);
          }}
        />
      )}

      {photoTarget && (
        <PhotoCaptureModal
          title={t.people.enrollPhotoModalTitle({ name: photoTarget.full_name })}
          onClose={() => setPhotoTarget(null)}
          onCapture={handlePhotoCapture}
          isSubmitting={isUploadingPhoto}
          error={photoError}
        />
      )}

      {teacherPhotoTarget && (
        <PhotoCaptureModal
          title={t.people.enrollPhotoModalTitle({ name: teacherPhotoTarget.full_name })}
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
  const { t } = useLanguage();
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
            showSuccess(t.people.toastStudentAddedWithPhoto);
          } catch (photoErr) {
            showError(t.people.toastStudentPhotoFailed({ reason: apiErrorMessage(photoErr) }));
          }
        } else {
          showSuccess(t.people.toastStudentAdded);
        }
      } else {
        const teacher = await createTeacher({ full_name: fullName, email: email || null });
        if (photo) {
          try {
            await uploadTeacherPhoto(teacher.id, photo);
            showSuccess(t.people.toastTeacherAddedWithPhoto);
          } catch (photoErr) {
            showError(t.people.toastTeacherPhotoFailed({ reason: apiErrorMessage(photoErr) }));
          }
        } else {
          showSuccess(t.people.toastTeacherAdded);
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
    <Modal
      title={tab === "students" ? t.people.addPersonModalTitleStudent : t.people.addPersonModalTitleTeacher}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <Field label={t.people.fieldFullName} value={fullName} onChange={setFullName} required />
        {tab === "students" && (
          <>
            <Field label={t.people.fieldStudentId} value={idNumber} onChange={setIdNumber} required />
            <Field label={t.people.fieldDepartment} value={department} onChange={setDepartment} />
          </>
        )}
        <Field label={t.people.fieldEmail} value={email} onChange={setEmail} type="email" />
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
            {t.people.photoFieldLabel}
          </label>
          <PhotoPicker value={photo} onChange={setPhoto} height={200} />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
        >
          {isSubmitting ? t.common.saving : t.common.save}
        </button>
      </form>
    </Modal>
  );
}

function ImportStudentsModal({
  onClose,
  onImported,
  onAddPhoto,
}: {
  onClose: () => void;
  onImported: () => void;
  onAddPhoto: (id: number, fullName: string, studentId: string) => void;
}) {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StudentImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const data = await importStudents(file);
      setResult(data);
      onImported();
      if (data.created > 0) {
        showSuccess(t.people.toastImported({ count: data.created }));
      }
      if (data.missing_photo > 0) {
        showError(t.people.toastMissingPhoto({ count: data.missing_photo }));
      }
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={t.people.importModalTitle} onClose={onClose}>
      {!result ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <p className="text-sm text-text-muted">{t.people.importHelp}</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.zip"
            required
            className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none file:mr-3 file:rounded-md file:border-0 file:bg-accent-soft file:px-3 file:py-1.5 file:text-accent"
          />
          {error && <p className="text-sm text-absent">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? t.common.importing : t.common.import}
          </button>
        </form>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <Stat label={t.people.importStatCreated} value={result.created} />
            <Stat label={t.people.importStatDuplicates} value={result.duplicates} />
            <Stat label={t.people.importStatInvalid} value={result.invalid} />
            <Stat label={t.people.importStatNoPhoto} value={result.missing_photo} />
          </div>

          {result.errors.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">
                {t.people.importSkippedRows}
              </p>
              <ul className="max-h-32 overflow-y-auto rounded-lg border border-border text-xs">
                {result.errors.map((e) => (
                  <li key={e.row} className="border-b border-border px-3 py-1.5 last:border-0">
                    {t.common.rowError({ row: e.row, reason: e.reason })}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.missing_photo_students.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">
                {t.people.importMissingPhotoHeader}
              </p>
              <ul className="max-h-48 overflow-y-auto rounded-lg border border-border text-sm">
                {result.missing_photo_students.map((s) => (
                  <li
                    key={s.id}
                    className="flex items-center justify-between border-b border-border px-3 py-2 last:border-0"
                  >
                    <span>
                      {s.full_name} <span className="text-text-muted">({s.student_id})</span>
                    </span>
                    <button
                      onClick={() => onAddPhoto(s.id, s.full_name, s.student_id)}
                      className="text-xs font-medium text-accent hover:underline"
                    >
                      {t.common.addPhoto}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-bg-inset"
          >
            {t.common.done}
          </button>
        </div>
      )}
    </Modal>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-bg-inset px-3 py-2">
      <div className="font-data text-lg font-semibold">{value}</div>
      <div className="text-xs text-text-muted">{label}</div>
    </div>
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
