import {useContext, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {format, toDate, addDays, isValid} from 'date-fns';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import DatePickerField from '@cscfi/shared/components/DatePickerField/DatePickerField';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import Dialog from '@cscfi/shared/components/Dialog/Dialog';
import {virkailijapalveluPatchEnddateMassUpdate$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../../Context';

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
    const [newEndDate, setNewEndDate] = useState<Date | undefined>(endDate);
    const [origEndDate, setOrigEndDate] = useState<Date>(endDate);
    const [initialNow] = useState<number>(() => Date.now());

    const toggleDialog = () => {
        setNewEndDate(origEndDate);
        setShowDialog(!showDialog);
    };

    const save = () => {
        virkailijapalveluPatchEnddateMassUpdate$(userInfo!)(
            id,
            koulutustoimija!,
            format(startDate!, 'yyyy-MM-dd'),
            {voimassa_loppupvm: format(newEndDate!, 'yyyy-MM-dd')},
        ).subscribe(() => {
            setOrigEndDate(newEndDate!);
            setShowDialog(!showDialog);
            const alert = {
                title: {
                    key: 'paattymispaivamaara-on-tallennettu',
                    ns: 'etusivu',
                },
                severity: 'success',
            } as AlertType;
            AlertService.showAlert(alert);
        });
    };

    const changeDate = (val: Date | null | undefined) => {
        if (isValid(val)) {
            setNewEndDate(toDate(val || ''));
        }
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
                {t('muuta-paattymispvm')}
            </button>
            {showDialog && (
                <Dialog
                    title={t('muuta-paattymispvm')}
                    confirm={save}
                    cancel={toggleDialog}
                    disableConfirm={!isValid(newEndDate)}
                    content={
                        <DatePickerField
                            label={t('paattymispaivamaara')}
                            date={newEndDate}
                            onChange={changeDate}
                            minDate={toDate(
                                Math.max(addDays(startDate, 1).getTime(), initialNow),
                            )}
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
