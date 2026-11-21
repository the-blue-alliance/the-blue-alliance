import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '~/components/ui/accordion';

function renderAccordion() {
  return render(
    <Accordion>
      <AccordionItem value="quals" className="group/item">
        <AccordionTrigger className="group/trigger">
          Qualification matches
        </AccordionTrigger>
        <AccordionContent className="group/content">
          Qual 1, Qual 2
        </AccordionContent>
      </AccordionItem>
    </Accordion>,
  );
}

describe('Accordion', () => {
  test('starts collapsed and merges classes onto the item and trigger', () => {
    renderAccordion();

    const trigger = screen.getByRole('button', {
      name: 'Qualification matches',
    });
    expect(trigger.className).toContain('group/trigger');
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(
      trigger.closest('[data-slot="accordion-item"]')?.className,
    ).toContain('group/item');
    expect(screen.queryByText('Qual 1, Qual 2')).toBeNull();
  });

  test('expands its panel when the trigger is clicked', () => {
    renderAccordion();

    fireEvent.click(
      screen.getByRole('button', { name: 'Qualification matches' }),
    );

    const content = screen.getByText('Qual 1, Qual 2');
    expect(content.className).toContain('group/content');
    expect(content.parentElement?.getAttribute('data-slot')).toBe(
      'accordion-content',
    );
  });
});
