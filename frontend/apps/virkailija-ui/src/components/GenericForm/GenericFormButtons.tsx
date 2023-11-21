import {useRef} from 'react';
import {useTranslation} from 'react-i18next';
import {useNavigate} from 'react-router-dom';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';

interface GenericFormButtonsProps {
    sourcePage?: string;
    needsCancelConfirmation?: boolean;
    hasPublishBtn?: boolean;
    translationNameSpace?: string;
}

function GenericFormButtons({
    sourcePage,
    needsCancelConfirmation,
    hasPublishBtn,
    translationNameSpace = 'genericform',
}: GenericFormButtonsProps) {
    const {t, i18n} = useTranslation([translationNameSpace]);
    const navigate = useNavigate();
    const publishRef = useRef<any | null>(null);

    function prevPage() {
        return sourcePage ? `/${sourcePage}` : '/';
    }

    return (
        <div className="button-container">
            {needsCancelConfirmation ? (
                <ConfirmationDialog
                    title={t('painike-takaisin-otsikko')}
                    confirm={() => navigate(prevPage())}
                    confirmBtnText={t('painike-takaisin-ok')}
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
            <button className="secondary" type="submit">
                {t('painike-tallenna-save')}
            </button>
            {!!hasPublishBtn && (
                <>
                    <button
                        type="submit"
                        value="publish"
                        ref={publishRef}
                        style={{display: 'none'}}
                    >
                        -
                    </button>
                    <ConfirmationDialog
                        title={t('painike-tallenna-publish-otsikko')}
                        confirm={() => publishRef.current.click()}
                        confirmBtnText={t('painike-tallenna-publish-ok')}
                        cancelBtnText={t('painike-tallenna-publish-cancel')}
                        content={
                            <>
                                <p>{t('painike-tallenna-publish-teksti-1')}</p>
                                {i18n.exists('painike-tallenna-publish-teksti-2') && (
                                    <p>{t('painike-tallenna-publish-teksti-2')}</p>
                                )}
                            </>
                        }
                    >
                        <button type="button">{t('painike-tallenna-publish')}</button>
                    </ConfirmationDialog>
                </>
            )}
        </div>
    );
}

export default GenericFormButtons;
