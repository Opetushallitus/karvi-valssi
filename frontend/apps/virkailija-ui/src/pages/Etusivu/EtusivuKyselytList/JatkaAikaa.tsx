import {useContext, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {format} from 'date-fns';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import DatePickerField from '@cscfi/shared/components/DatePickerField/DatePickerField';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import Dialog from '@cscfi/shared/components/Dialog/Dialog';
// eslint-disable-next-line max-len
import {virkailijapalveluPatchEnddateMassUpdate$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../../Context';

// eslint-disable-next-line max-len

interface KyselyLinkProps {
    kysely: KyselyType;
    koulutustoimija: string | undefined;
    startDate: Date;
    endDate: Date;
}

function JatkaAikaa({kysely, koulutustoimija, startDate, endDate}: KyselyLinkProps) {
    const {id} = kysely;
    const {t} = useTranslation(['etusivu']);
    const userInfo = useContext(UserContext);
    const [showDialog, setShowDialog] = useState<boolean>(false);
    const [newEndDate, setNewEndDate] = useState<Date | null | undefined>(endDate);
    const [origEndDate, setOrigEndDate] = useState<Date>(endDate);
    const PatchEnddateMassUpdate = (koulutustoimOid: string, body: any) =>
        virkailijapalveluPatchEnddateMassUpdate$(userInfo!)(
            id,
            koulutustoimOid,
            format(startDate!, 'yyyy-MM-dd'),
            body,
        );

    const toggleDialog = () => {
        setNewEndDate(origEndDate);
        setShowDialog(!showDialog);
    };
    const save = () => {
        if (newEndDate instanceof Date) setOrigEndDate(newEndDate);
        setShowDialog(!showDialog);
        const requestBody = {voimassa_loppupvm: format(newEndDate!, 'yyyy-MM-dd')};
        if (koulutustoimija) {
            PatchEnddateMassUpdate(koulutustoimija, requestBody).subscribe(() => {
                const alert = {
                    title: {
                        key: 'paattymispaivamaara-on-tallennettu',
                        ns: 'etusivu',
                    },
                    severity: 'success',
                } as AlertType;
                AlertService.showAlert(alert);
            });
        }
    };
    const changeDate = (val: Date | null | undefined) => {
        setNewEndDate(val);
    };
    return (
        <>
            <button
                type="button"
                onClick={() => {
                    toggleDialog();
                }}
                className="small"
            >
                {t('jatka-vastausaikaa')}
            </button>
            {showDialog && (
                <Dialog
                    title={t('jatka-vastausaikaa')}
                    confirm={save}
                    cancel={toggleDialog}
                    disableConfirm={!(newEndDate?.getTime()! > endDate?.getTime())}
                    content={
                        <DatePickerField
                            label={t('paattymispaivamaara')}
                            date={newEndDate}
                            onChange={changeDate}
                            minDate={origEndDate}
                        />
                    }
                    confirmBtnText={t('painike-tallenna')}
                    showDialogBoolean
                />
            )}
        </>
    );
}

export default JatkaAikaa;
