import {useTranslation} from 'react-i18next';
import {useNavigate} from 'react-router-dom';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';

interface RaporttipohjaButtonsProps {
    sourcePage?: string;
    needsCancelConfirmation?: boolean;
    kysymysryhmaId: number;
    onPreviewClick: () => void;
}

function RaportointiPohjaButtons({
    sourcePage,
    needsCancelConfirmation,
    kysymysryhmaId,
    onPreviewClick,
}: RaporttipohjaButtonsProps) {
    const {t, i18n} = useTranslation(['raporttipohja']);
    const navigate = useNavigate();

    const urlLink = `/raportointipohja/esikatselu?raportti=${kysymysryhmaId}`;

    function prevPage() {
        return sourcePage ? `/${sourcePage}` : '/';
    }

    return (
        <div className="button-container">
            {needsCancelConfirmation ? (
                <ConfirmationDialog
                    title={t('painike-takaisin-otsikko')}
                    confirm={() => {
                        sessionStorage.removeItem(`reportPreviewData_${kysymysryhmaId}`);
                        navigate(prevPage());
                    }}
                    confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                    cancelBtnText={t('painike-takaisin-cancel')}
                    content={
                        <>
                            <p>{t('painike-takaisin-teksti-1')}</p>
                            {i18n.exists('painike-takaisin-teksti-2') && (
                                <p>{t('painike-takaisin-teksti-2')}</p>
                            )}
                        </>
                    }
                >
                    <button type="button" className="secondary">
                        {t('painike-takaisin')}
                    </button>
                </ConfirmationDialog>
            ) : (
                <button
                    type="button"
                    className="secondary"
                    onClick={() => navigate(prevPage())}
                >
                    {t('painike-takaisin')}
                </button>
            )}
            <ButtonWithLink
                linkTo={urlLink}
                linkText={t('painike-esikatselu')}
                className="secondary"
                onClick={onPreviewClick}
            />
            <button type="submit">{t('painike-tallenna', {ns: 'yleiset'})}</button>
        </div>
    );
}

export default RaportointiPohjaButtons;
