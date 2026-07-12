import { useLanguage } from "../context/LanguageContext";

export function TableLoading({ colSpan }: { colSpan: number }) {
  const { t } = useLanguage();
  return (
    <tr>
      <td colSpan={colSpan} className="py-10 text-center text-sm text-text-muted">
        {t.common.loading}
      </td>
    </tr>
  );
}

export function TableEmpty({ colSpan, message }: { colSpan: number; message?: string }) {
  const { t } = useLanguage();
  return (
    <tr>
      <td colSpan={colSpan} className="py-10 text-center text-sm text-text-muted">
        {message ?? t.common.noRecords}
      </td>
    </tr>
  );
}
